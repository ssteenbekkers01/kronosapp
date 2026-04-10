import os
import sqlite3
import pandas as pd

DB_FILE = "data/predictions.db"
EXCEL_FILE = "data/predictions.xlsx"
CSV_FILE = "data/all_predictions.csv"

# -----------------------------
# STEP 1: LOAD AND VALIDATE CSV
# -----------------------------
if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

new_data = pd.read_csv(CSV_FILE)

# Normalize column names
new_data.columns = [col.lower().strip() for col in new_data.columns]

# Rename common variants just in case
rename_map = {
    "date": "timestamps",
    "datetime": "timestamps",
    "timestamp": "timestamps",
}
new_data = new_data.rename(columns=rename_map)

required_cols = ["ticker", "timestamps", "open", "high", "low", "close"]
missing = [col for col in required_cols if col not in new_data.columns]

if missing:
    raise ValueError(
        f"Missing required columns in {CSV_FILE}: {missing}. "
        f"Found columns: {list(new_data.columns)}"
    )

# Keep only required columns
new_data = new_data[required_cols].copy()

# Parse timestamps
new_data["timestamps"] = pd.to_datetime(new_data["timestamps"], errors="coerce")

if new_data["timestamps"].isna().any():
    raise ValueError("Invalid timestamps detected")

# Parse numeric OHLC
for col in ["open", "high", "low", "close"]:
    new_data[col] = pd.to_numeric(new_data[col], errors="coerce")

if new_data[["open", "high", "low", "close"]].isna().any().any():
    raise ValueError("Invalid OHLC values detected")

# Add run timestamp
run_timestamp = pd.Timestamp.now()
new_data["run_timestamp"] = run_timestamp

# Convert to strings for SQLite
new_data["timestamps"] = new_data["timestamps"].dt.strftime("%Y-%m-%d %H:%M:%S")
new_data["run_timestamp"] = new_data["run_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

# -----------------------------
# STEP 2: WRITE TO SQLITE
# -----------------------------
conn = sqlite3.connect(DB_FILE)

create_table_query = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    timestamps TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    run_timestamp TEXT NOT NULL,
    UNIQUE(ticker, timestamps)
)
"""
conn.execute(create_table_query)

rows_inserted = 0

for _, row in new_data.iterrows():
    cursor = conn.execute("""
        INSERT OR IGNORE INTO predictions
        (ticker, timestamps, open, high, low, close, run_timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        row["ticker"],
        row["timestamps"],
        row["open"],
        row["high"],
        row["low"],
        row["close"],
        row["run_timestamp"]
    ))

    if cursor.rowcount > 0:
        rows_inserted += 1

# 🔑 THIS WAS MISSING
conn.commit()

print(f"Inserted {rows_inserted} new rows into SQLite")

# -----------------------------
# STEP 3: EXPORT LAST 30 DAYS
# -----------------------------
query = """
SELECT ticker, timestamps, open, high, low, close, run_timestamp
FROM predictions
WHERE run_timestamp >= datetime('now', '-30 days')
ORDER BY run_timestamp DESC, ticker ASC, timestamps ASC
"""

recent_data = pd.read_sql_query(query, conn)

conn.close()

# Convert back to datetime for Excel
for col in ["timestamps", "run_timestamp"]:
    if col in recent_data.columns:
        recent_data[col] = pd.to_datetime(recent_data[col], errors="coerce")

if recent_data.empty:
    raise ValueError("No recent data found in SQLite")

latest_run_time = recent_data["run_timestamp"].max()
latest_df = recent_data[recent_data["run_timestamp"] == latest_run_time].copy()

with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="w") as writer:
    latest_df.to_excel(writer, sheet_name="Latest", index=False)
    recent_data.to_excel(writer, sheet_name="Recent_History", index=False)

print(f"Updated Excel export: {EXCEL_FILE}")
print(f"Latest run timestamp: {latest_run_time}")