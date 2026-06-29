import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)


# =====================================================
# 1. BASIC MEMBERSHIP FUNCTIONS
# =====================================================
def tri_left(x, a, b):
    if pd.isna(x):
        return 0.0
    if x <= a:
        return 1.0
    if x >= b:
        return 0.0
    return (b - x) / (b - a)


def tri_right(x, a, b):
    if pd.isna(x):
        return 0.0
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    return (x - a) / (b - a)


def tent(x, a, m, b):
    if pd.isna(x):
        return 0.0
    if x <= a or x >= b:
        return 0.0
    if x == m:
        return 1.0
    if x < m:
        return (x - a) / (m - a)
    return (b - x) / (b - m)


# =====================================================
# 2. OUTPUT MEMBERSHIP
# =====================================================
def out_not_pot(x):
    return tri_left(x, 0.0, 0.4)


def out_neutral(x):
    return tent(x, 0.25, 0.5, 0.75)


def out_pot(x):
    return tri_right(x, 0.6, 1.0)


# =====================================================
# 3. FUZZY MAMDANI ENGINE
# =====================================================
class FuzzyMamdaniEngine:

    def __init__(self, sector_stats: pd.DataFrame, rules_df: pd.DataFrame):
        self.sector_stats = sector_stats.copy()
        self.sector_stats.index = self.sector_stats.index.astype(str).str.strip()

        self.rules_df = rules_df.copy()

        # Kolom database seperti id_rule, eps, per, horizon akan jadi uppercase
        self.rules_df.columns = [str(c).strip().upper() for c in self.rules_df.columns]

        self.rules_df.replace(["-", "", " "], np.nan, inplace=True)

        if "GRADIENT" in self.rules_df.columns and "GRADIEN" not in self.rules_df.columns:
            self.rules_df["GRADIEN"] = self.rules_df["GRADIENT"]

        if "GRADIEN" in self.rules_df.columns and "GRADIENT" not in self.rules_df.columns:
            self.rules_df["GRADIENT"] = self.rules_df["GRADIEN"]

        self.x_grid = np.linspace(0, 1, 101)

    # =================================================
    # HELPER
    # =================================================
    def _get_value(self, row, *names, default=np.nan):
        for name in names:
            if name in row.index:
                return row.get(name)
        return default

    def _get_rule_value(self, rule, *names):
        if rule is None:
            return None

        for name in names:
            name_upper = str(name).strip().upper()

            if name_upper in rule.index:
                value = rule.get(name_upper)

                if pd.notna(value) and str(value).strip() not in ["", "-", "nan", "None"]:
                    return value

        return None

    # =================================================
    # MEMBERSHIP GENERATORS
    # =================================================
    def stat_mb(self, v, mean, std):
        if pd.isna(v) or pd.isna(mean) or pd.isna(std) or std == 0:
            return {"low": 0.0, "mid": 0.0, "high": 0.0}

        lo, hi = mean - std, mean + std

        return {
            "low": float(tri_left(v, lo, mean)),
            "mid": float(tent(v, lo, mean, hi)),
            "high": float(tri_right(v, mean, hi))
        }

    def ma_mb(self, price, ma):
        if pd.isna(price) or pd.isna(ma) or ma == 0:
            return {"bear": 0.0, "netral": 0.0, "bull": 0.0}

        d = (price - ma) / ma

        return {
            "bear": float(tri_left(d, -0.02, 0.0)),
            "netral": float(tent(d, -0.02, 0.0, 0.02)),
            "bull": float(tri_right(d, 0.0, 0.02))
        }

    def gradient_mb(self, g):
        if pd.isna(g):
            return {"negatif": 0.0, "netral": 0.0, "positif": 0.0}

        return {
            "negatif": float(tri_left(g, -0.01, 0.0)),
            "netral": float(tent(g, -0.01, 0.0, 0.01)),
            "positif": float(tri_right(g, 0.0, 0.01))
        }

    def volume_mb(self, v, vma):
        if pd.isna(v) or pd.isna(vma) or vma == 0:
            return {"low": 0.0, "mid": 0.0, "high": 0.0}

        d = (v - vma) / vma

        return {
            "low": float(tri_left(d, -0.20, 0.0)),
            "mid": float(tent(d, -0.20, 0.0, 0.20)),
            "high": float(tri_right(d, 0.0, 0.20))
        }

    def rsi_mb(self, r):
        if pd.isna(r):
            return {"oversold": 0.0, "netral": 0.0, "overbought": 0.0}

        return {
            "oversold": float(tri_left(r, 30, 50)),
            "netral": float(tent(r, 30, 50, 70)),
            "overbought": float(tri_right(r, 50, 70))
        }

    # =================================================
    # RULE MATCHING
    # =================================================
    def _match(self, mb: dict, label):
        if pd.isna(label):
            return 1.0

        label = str(label).strip().lower()

        if label in ["", "-", "nan", "none"]:
            return 1.0

        mapping = {
            "low": "low",
            "rendah": "low",

            "mid": "mid",
            "sedang": "mid",

            "high": "high",
            "tinggi": "high",

            "bear": "bear",
            "bearish": "bear",

            "bull": "bull",
            "bullish": "bull",

            "negatif": "negatif",
            "negative": "negatif",

            "netral": "netral",
            "net": "netral",
            "neutral": "netral",

            "positif": "positif",
            "positive": "positif",

            "oversold": "oversold",
            "overbought": "overbought"
        }

        key = mapping.get(label)

        if key is None:
            return 1.0

        return float(mb.get(key, 0.0))

    def _build_rule_condition(self, rule):
        if rule is None:
            return None

        cols = [
            ("EPS", "EPS"),
            ("PER", "PER"),
            ("ROE", "ROE"),
            ("FCF", "FCF"),
            ("DER", "DER"),
            ("MA50", "MA50"),
            ("MA200", "MA200"),
            ("GRADIEN", "Gradien"),
            ("VOLUME", "Volume"),
            ("RSI", "RSI"),
            ("SENTIMEN", "Sentimen")
        ]

        parts = []

        for col, label in cols:
            value = self._get_rule_value(rule, col)

            if value is not None:
                parts.append(f"{label}: {value}")

        return ", ".join(parts) if parts else None

    def evaluate(self, row: pd.Series):
        sector = str(self._get_value(row, "Sektor", "SEKTOR", "sector", "Sector", default="")).strip()

        if sector in self.sector_stats.index:
            stats = self.sector_stats.loc[sector]
        else:
            stats = self.sector_stats.mean(numeric_only=True)

        close_price = self._get_value(row, "close_price", "Close", "harga", "Harga")
        gradien_value = self._get_value(row, "gradien", "gradient", "GRADIEN", "GRADIENT")
        sent_v = self._get_value(row, "sent_v", "sentimen_v", "sentiment_value", default=0.5)

        # ===============================
        # HITUNG MEMBERSHIP
        # ===============================
        mbs = {
            "EPS": self.stat_mb(
                self._get_value(row, "eps", "EPS"),
                stats.get("eps_mean"),
                stats.get("eps_std")
            ),
            "PER": self.stat_mb(
                self._get_value(row, "per", "PER"),
                stats.get("per_mean"),
                stats.get("per_std")
            ),
            "ROE": self.stat_mb(
                self._get_value(row, "roe", "ROE"),
                stats.get("roe_mean"),
                stats.get("roe_std")
            ),
            "FCF": self.stat_mb(
                self._get_value(row, "fcf", "FCF"),
                stats.get("fcf_mean"),
                stats.get("fcf_std")
            ),
            "DER": self.stat_mb(
                self._get_value(row, "der", "DER"),
                stats.get("der_mean"),
                stats.get("der_std")
            ),
            "MA50": self.ma_mb(
                close_price,
                self._get_value(row, "ma50", "MA50")
            ),
            "MA200": self.ma_mb(
                close_price,
                self._get_value(row, "ma200", "MA200")
            ),
            "GRADIEN": self.gradient_mb(gradien_value),
            "GRADIENT": self.gradient_mb(gradien_value),
            "VOLUME": self.volume_mb(
                self._get_value(row, "volume", "Volume", "VOLUME"),
                self._get_value(row, "volma200", "VolMA200", "VOLMA200")
            ),
            "RSI": self.rsi_mb(
                self._get_value(row, "rsi", "RSI")
            ),
            "SENTIMEN": {
                "negatif": 1.0 if sent_v == 0.0 else 0.0,
                "netral": 1.0 if sent_v == 0.5 else 0.0,
                "positif": 1.0 if sent_v == 1.0 else 0.0
            }
        }

        # ===============================
        # INFERENSI
        # ===============================
        agg = np.zeros_like(self.x_grid)
        max_alpha = -1.0
        dom_rule = None

        for _, rule in self.rules_df.iterrows():
            alpha = min(
                self._match(mbs["EPS"], self._get_rule_value(rule, "EPS")),
                self._match(mbs["PER"], self._get_rule_value(rule, "PER")),
                self._match(mbs["ROE"], self._get_rule_value(rule, "ROE")),
                self._match(mbs["FCF"], self._get_rule_value(rule, "FCF")),
                self._match(mbs["DER"], self._get_rule_value(rule, "DER")),
                self._match(mbs["MA50"], self._get_rule_value(rule, "MA50")),
                self._match(mbs["MA200"], self._get_rule_value(rule, "MA200")),
                self._match(mbs["GRADIEN"], self._get_rule_value(rule, "GRADIEN", "GRADIENT")),
                self._match(mbs["VOLUME"], self._get_rule_value(rule, "VOLUME")),
                self._match(mbs["RSI"], self._get_rule_value(rule, "RSI")),
                self._match(mbs["SENTIMEN"], self._get_rule_value(rule, "SENTIMEN"))
            )

            if alpha <= 0:
                continue

            if alpha > max_alpha:
                max_alpha = alpha
                dom_rule = rule

            out_label = str(self._get_rule_value(rule, "OUTPUT") or "").strip().lower()

            if "tidak" in out_label or "not" in out_label:
                mf = out_not_pot
            elif "pot" in out_label:
                mf = out_pot
            else:
                mf = out_neutral

            output_values = np.array([mf(x) for x in self.x_grid])
            agg = np.maximum(agg, np.minimum(alpha, output_values))

        # ===============================
        # DEFUZZIFIKASI
        # ===============================
        if np.sum(agg) > 0:
            score = np.sum(self.x_grid * agg) / np.sum(agg)
        else:
            score = 0.5

        label = (
            "Potensial" if score >= 0.75 else
            "Tidak Potensial" if score <= 0.25 else
            "Netral"
        )

        rule_id = None
        horizon = None
        rule_condition = None

        if dom_rule is not None:
            rule_id = self._get_rule_value(dom_rule, "ID_RULE")
            horizon = self._get_rule_value(dom_rule, "HORIZON")
            rule_condition = self._build_rule_condition(dom_rule)

        return {
            "score": round(float(score), 4),
            "label": label,
            "rule_id": None if rule_id is None or pd.isna(rule_id) else str(rule_id),
            "horizon": None if horizon is None or pd.isna(horizon) else str(horizon),
            "rule_condition": None if rule_condition is None or pd.isna(rule_condition) else str(rule_condition),
            "firing_strength": round(float(max_alpha), 4) if max_alpha >= 0 else 0.0,
            "mbs": mbs
        }