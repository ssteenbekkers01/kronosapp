from src.utils.telegram import send_alert
import os
import pandas as pd
import sqlite3

DB_FILE = "data/predictions.db"
DATA_DIR = "data"

conn = sqlite3.connect(DB_FILE)

# Create evaluations table immediately
create_table_query = """
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT,
    prediction_date TEXT,
    previous_close REAL,
    predicted_close REAL,
    actual_close REAL,
    predicted_return REAL,
    actual_return REAL,
    predicted_direction TEXT,
    actual_direction TEXT,
    direction_correct BOOLEAN,
    error REAL,
    abs_error REAL,
    run_timestamp TEXT

)
"""
conn.execute(create_table_query)
conn.commit()

# Load predictions from SQLite
query = """
SELECT ticker, timestamps, close, run_timestamp
FROM predictions
"""
pred_df = pd.read_sql_query(query, conn)

if pred_df.empty:
    print("No predictions found in database.")
    conn.close()
    exit()

pred_df["timestamps"] = pd.to_datetime(pred_df["timestamps"], errors="coerce")

results = []
checked_count = 0
future_count = 0

for _, row in pred_df.iterrows():
    ticker = row["ticker"]
    prediction_date = row["timestamps"]
    predicted_close = row["close"]
    run_timestamp = row["run_timestamp"]

    file_path = os.path.join(DATA_DIR, f"{ticker}.csv")

    if not os.path.exists(file_path):
        print(f"{ticker}: no local data file found")
        continue

    actual_data = pd.read_csv(file_path)
    actual_data.columns = [col.lower() for col in actual_data.columns]

    if "date" not in actual_data.columns or "close" not in actual_data.columns:
        print(f"{ticker}: missing required columns in CSV")
        continue

    actual_data["date"] = pd.to_datetime(actual_data["date"], errors="coerce")
    latest_actual_date = actual_data["date"].max()

    if prediction_date > latest_actual_date:
        future_count += 1
        continue

    match = actual_data[actual_data["date"] == prediction_date]
    if match.empty:
        continue

    previous_rows = actual_data[actual_data["date"] < prediction_date].sort_values("date")
    if previous_rows.empty:
        continue

    previous_close = previous_rows.iloc[-1]["close"]
    actual_close = match.iloc[0]["close"]

    predicted_direction = "up" if predicted_close > previous_close else "down"
    actual_direction = "up" if actual_close > previous_close else "down"
    direction_correct = predicted_direction == actual_direction
    predicted_return = (predicted_close - previous_close) / previous_close
    actual_return = (actual_close - previous_close) / previous_close

    error = actual_close - predicted_close
    abs_error = abs(error)

    results.append({
        "ticker": ticker,
        "prediction_date": prediction_date.strftime("%Y-%m-%d"),
        "previous_close": previous_close,
        "predicted_close": predicted_close,
        "actual_close": actual_close,
        "predicted_direction": predicted_direction,
        "actual_direction": actual_direction,
        "direction_correct": direction_correct,
        "error": error,
        "abs_error": abs_error,
        "run_timestamp": run_timestamp,
        "predicted_return": predicted_return,
        "actual_return": actual_return
    })

    checked_count += 1
    print(f"{ticker}: evaluated {prediction_date.date()}")

if results:
    new_results = pd.DataFrame(results)

    # remove duplicates within this batch
    new_results = new_results.drop_duplicates(subset=["ticker", "prediction_date"])

    # load existing keys from DB
    existing = pd.read_sql_query(
        "SELECT ticker, prediction_date FROM evaluations",
        conn
    )

    # remove rows that already exist in DB
    new_results = new_results.merge(
        existing,
        on=["ticker", "prediction_date"],
        how="left",
        indicator=True
    )

    new_results = new_results[new_results["_merge"] == "left_only"]
    new_results = new_results.drop(columns=["_merge"])

    # insert only new rows
    if not new_results.empty:
        new_results.to_sql("evaluations", conn, if_exists="append", index=False)
        conn.commit()
        print(f"\nSaved {len(new_results)} NEW evaluation rows to SQLite")
    else:
        print("\nNo new evaluation rows to insert (duplicates skipped)")
else:
    print("No evaluation results were created yet.")

conn.close()

if results:
    eval_df = pd.DataFrame(results)

    if not eval_df.empty:
        win_rate = (eval_df["direction_correct"] == True).mean() * 100
        avg_actual_return = eval_df["actual_return"].mean() * 100

        send_alert(
            f"📊 Kronos evaluation summary\n"
            f"Evaluated: {len(eval_df)}\n"
            f"Win rate: {win_rate:.1f}%\n"
            f"Avg actual return: {avg_actual_return:.2f}%"
        )