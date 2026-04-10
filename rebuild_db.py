import sqlite3
import pandas as pd
import os

DB_FILE = "data/predictions.db"
CSV_FILE = "data/all_predictions.csv"

# -----------------------------
# LOAD CSV
# -----------------------------
if not os.path.exists(CSV_FILE):
    raise FileNotFoundError("CSV not found")

df = pd.read_csv(CSV_FILE)

# Normalize columns
df.columns = [col.lower().strip() for col in df.columns]

rename_map = {
    "date": "timestamps",
    "datetime": "timestamps",
    "timestamp": "timestamps",
}
df = df.rename(columns=rename_map)

required = ["ticker", "timestamps", "open", "high", "low", "close"]
missing = [col for col in required if col not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

# Clean types
df["timestamps"] = pd.to_datetime(df["timestamps"], errors="coerce")
df = df.dropna(subset=["timestamps"])

for col in ["open", "high", "low", "close"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna()

# Add run_timestamp (same for all imported rows)
df["run_timestamp"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

# Convert timestamps to string
df["timestamps"] = df["timestamps"].dt.strftime("%Y-%m-%d %H:%M:%S")

# -----------------------------
# CREATE DB + TABLE
# -----------------------------
conn = sqlite3.connect(DB_FILE)

conn.execute("""
CREATE TABLE predictions (
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
""")

# -----------------------------
# INSERT (NO DUPLICATES)
# -----------------------------
for _, row in df.iterrows():
    conn.execute("""
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

conn.commit()
conn.close()

print("Database rebuilt cleanly with UNIQUE constraint")