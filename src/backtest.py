import sqlite3
import pandas as pd

DB_PATH = "data/predictions.db"


def run_backtest():
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        e.ticker,
        e.prediction_date,
        e.previous_close,
        e.predicted_close,
        e.actual_close,
        e.direction_correct,
        e.error,
        e.abs_error
    FROM evaluations e
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        print("No evaluation data found")
        conn.close()
        return

    df["prediction_date"] = pd.to_datetime(df["prediction_date"])

    # remove duplicate ticker/date rows
    df = df.drop_duplicates(subset=["ticker", "prediction_date"], keep="first")

    # calculate returns
    df["realized_return"] = (df["actual_close"] - df["previous_close"]) / df["previous_close"]
    df["predicted_return"] = (df["predicted_close"] - df["previous_close"]) / df["previous_close"]

    # rank by predicted return
    df = df.sort_values(["prediction_date", "predicted_return"], ascending=[True, False])

    # pick top 3 per day
    df["rank"] = df.groupby("prediction_date").cumcount() + 1
    df = df[df["rank"] <= 3]

    print("Total trades:", len(df))
    print("Unique prediction dates:", df["prediction_date"].nunique())
    print("Win rate:", round((df["realized_return"] > 0).mean(), 2))
    print("Average realized return:", round(df["realized_return"].mean(), 4))
    print("Total realized return:", round(df["realized_return"].sum(), 4))
    print("Direction accuracy:", round(df["direction_correct"].mean(), 2))
    print()
    print(df[[
        "ticker",
        "prediction_date",
        "predicted_return",
        "realized_return",
        "direction_correct",
        "rank"
    ]].head(10))

    conn.close()


if __name__ == "__main__":
    run_backtest()
