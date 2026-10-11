import re
from pathlib import Path

src = Path("binlog_109_145.txt")
out = Path("restore_stock_realtime.sql")
lines = src.read_text(encoding="utf-8", errors="replace").splitlines()

rows = []
active = False
current = None

for line in lines:
    if re.search(r"### INSERT INTO `[^`]+`\.`stock_realtime`", line):
        active = True
        current = None
        continue

    if line.startswith("### INSERT INTO ") or line.startswith("### UPDATE ") or line.startswith("### DELETE "):
        active = False
        current = None
        continue

    if line.startswith("# at "):
        active = False
        current = None
        continue

    if not active:
        continue

    if line.strip() == "### SET":
        if current and len(current) == 21:
            rows.append(current)
        current = {}
        continue

    m = re.match(r"###\s+@(\d+)=(.*)$", line)
    if m and current is not None:
        idx = int(m.group(1))
        value = re.sub(r"\s+/\*.*\*/\s*$", "", m.group(2)).strip()
        current[idx] = value

if current and len(current) == 21:
    rows.append(current)

columns = [
    "id_realtime", "id_stock", "snapshot_at", "eps", "per",
    "roe", "der", "fcf", "close_price", "volume", "ma50",
    "ma200", "volma200", "rsi", "gradient", "sentimen",
    "fuzzy_score", "kategori", "horizon", "insight", "created_at"
]

with out.open("w", encoding="utf-8", newline="\n") as f:
    f.write("USE `fuzzy_saham_restore`;\n")
    for row in rows:
        values = ", ".join(row[i] for i in range(1, 22))
        f.write(
            "INSERT IGNORE INTO `stock_realtime` "
            f"({', '.join('`' + c + '`' for c in columns)}) "
            f"VALUES ({values});\n"
        )

print(f"Total baris INSERT ditemukan: {len(rows)}")
print(f"File SQL dibuat: {out.resolve()}")
