import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

# =====================================================
# 1. BASIC MEMBERSHIP FUNCTIONS
# =====================================================
def tri_left(x, a, b):
    if pd.isna(x): return 0.0
    if x <= a: return 1.0
    if x >= b: return 0.0
    return (b - x) / (b - a)

def tri_right(x, a, b):
    if pd.isna(x): return 0.0
    if x <= a: return 0.0
    if x >= b: return 1.0
    return (x - a) / (b - a)

def tent(x, a, m, b):
    if pd.isna(x): return 0.0
    if x <= a or x >= b: return 0.0
    if x == m: return 1.0
    if x < m: return (x - a) / (m - a)
    return (b - x) / (b - m)

# =====================================================
# OUTPUT MEMBERSHIP
# =====================================================
def out_not_pot(x): return tri_left(x, 0.0, 0.4)
def out_neutral(x): return tent(x, 0.25, 0.5, 0.75)
def out_pot(x): return tri_right(x, 0.6, 1.0)

# =====================================================
# FUZZY MAMDANI ENGINE
# =====================================================
class FuzzyMamdaniEngine:

    def __init__(self, sector_stats: pd.DataFrame, rules_df: pd.DataFrame):
        """
        sector_stats:
            index = Sektor
            kolom = eps_mean, eps_std, per_mean, per_std, dst
        rules_df:
            tabel rule dari database
        """
        self.sector_stats = sector_stats.copy()

        # Normalisasi rule
        self.rules_df = rules_df.copy()
        self.rules_df.columns = [str(c).strip().upper() for c in self.rules_df.columns]
        self.rules_df.replace(["-", "", " "], np.nan, inplace=True)

        self.x_grid = np.linspace(0, 1, 101)

    # =================================================
    # MEMBERSHIP GENERATORS
    # =================================================
    def stat_mb(self, v, mean, std):
        if pd.isna(v) or pd.isna(mean) or pd.isna(std) or std == 0:
            return {"low": 0.0, "mid": 0.0, "high": 0.0}

        lo, hi = mean - std, mean + std
        return {
            "low": tri_left(v, lo, mean),
            "mid": tent(v, lo, mean, hi),
            "high": tri_right(v, mean, hi)
        }

    def ma_mb(self, price, ma):
        if pd.isna(price) or pd.isna(ma) or ma == 0:
            return {"bear": 0.0, "netral": 0.0, "bull": 0.0}

        d = (price - ma) / ma
        return {
            "bear": tri_left(d, -0.02, 0.0),
            "netral": tent(d, -0.02, 0.0, 0.02),
            "bull": tri_right(d, 0.0, 0.02)
        }

    def gradient_mb(self, g):
        if pd.isna(g):
            return {"negatif": 0.0, "netral": 0.0, "positif": 0.0}

        return {
            "negatif": tri_left(g, -0.01, 0.0),
            "netral": tent(g, -0.01, 0.0, 0.01),
            "positif": tri_right(g, 0.0, 0.01)
        }

    def volume_mb(self, v, vma):
        if pd.isna(v) or pd.isna(vma) or vma == 0:
            return {"low": 0.0, "mid": 0.0, "high": 0.0}

        d = (v - vma) / vma
        return {
            "low": tri_left(d, -0.20, 0.0),
            "mid": tent(d, -0.20, 0.0, 0.20),
            "high": tri_right(d, 0.0, 0.20)
        }

    def rsi_mb(self, r):
        if pd.isna(r):
            return {"oversold": 0.0, "netral": 0.0, "overbought": 0.0}

        return {
            "oversold": tri_left(r, 30, 50),
            "netral": tent(r, 30, 50, 70),
            "overbought": tri_right(r, 50, 70)
        }

    # =================================================
    # RULE MATCHING (TOLERANT & AMAN)
    # =================================================
    def _match(self, mb: dict, label):
        if pd.isna(label):
            return 1.0

        label = str(label).strip().lower()
        if label in ["", "-", "nan"]:
            return 1.0

        mapping = {
            "low": "low", "mid": "mid", "high": "high",
            "bear": "bear", "bull": "bull",
            "negatif": "negatif", "positif": "positif",
            "netral": "netral", "net": "netral",
            "oversold": "oversold",
            "overbought": "overbought"
        }

        key = mapping.get(label)
        return float(mb.get(key, 0.0)) if key else 1.0

    # =================================================
    # MAIN EVALUATION
    # =================================================
    def evaluate(self, row: pd.Series):
        sector = row.get("Sektor")

        stats = (
            self.sector_stats.loc[sector]
            if sector in self.sector_stats.index
            else self.sector_stats.mean()
        )

        # ===============================
        # HITUNG MEMBERSHIP
        # ===============================
        mbs = {
            "EPS": self.stat_mb(row.get("eps"), stats.get("eps_mean"), stats.get("eps_std")),
            "PER": self.stat_mb(row.get("per"), stats.get("per_mean"), stats.get("per_std")),
            "ROE": self.stat_mb(row.get("roe"), stats.get("roe_mean"), stats.get("roe_std")),
            "FCF": self.stat_mb(row.get("fcf"), stats.get("fcf_mean"), stats.get("fcf_std")),
            "DER": self.stat_mb(row.get("der"), stats.get("der_mean"), stats.get("der_std")),
            "MA50": self.ma_mb(row.get("close_price"), row.get("ma50")),
            "MA200": self.ma_mb(row.get("close_price"), row.get("ma200")),
            "GRADIENT": self.gradient_mb(row.get("gradient")),
            "VOLUME": self.volume_mb(row.get("volume"), row.get("volma200")),
            "RSI": self.rsi_mb(row.get("rsi")),
            "SENTIMEN": {
                "negatif": 1.0 if row.get("sent_v") == 0.0 else 0.0,
                "netral": 1.0 if row.get("sent_v") == 0.5 else 0.0,
                "positif": 1.0 if row.get("sent_v") == 1.0 else 0.0
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
                self._match(mbs["EPS"], rule.get("EPS")),
                self._match(mbs["PER"], rule.get("PER")),
                self._match(mbs["ROE"], rule.get("ROE")),
                self._match(mbs["FCF"], rule.get("FCF")),
                self._match(mbs["DER"], rule.get("DER")),
                self._match(mbs["MA50"], rule.get("MA50")),
                self._match(mbs["MA200"], rule.get("MA200")),
                self._match(mbs["GRADIENT"], rule.get("GRADIENT")),
                self._match(mbs["VOLUME"], rule.get("VOLUME")),
                self._match(mbs["RSI"], rule.get("RSI")),
                self._match(mbs["SENTIMEN"], rule.get("SENTIMEN"))
            )

            if alpha <= 0:
                continue

            if alpha > max_alpha:
                max_alpha = alpha
                dom_rule = rule

            out_label = str(rule.get("OUTPUT", "")).lower()
            if "tidak" in out_label or "not" in out_label:
                mf = out_not_pot
            elif "pot" in out_label:
                mf = out_pot
            else:
                mf = out_neutral

            agg = np.maximum(
                agg,
                np.minimum(alpha, [mf(x) for x in self.x_grid])
            )

        # ===============================
        # DEFUZZIFIKASI
        # ===============================
        score = (
            np.sum(self.x_grid * agg) / np.sum(agg)
            if np.sum(agg) > 0 else 0.5
        )

        label = (
            "Potensial" if score >= 0.75 else
            "Tidak Potensial" if score <= 0.25 else
            "Netral"
        )

        return {
            "score": round(score, 4),
            "label": label,
            "rule_id": dom_rule.get("RULE") if dom_rule is not None else None,
            "horizon": dom_rule.get("HORIZON") if dom_rule is not None else None,
            "mbs": mbs
        }
