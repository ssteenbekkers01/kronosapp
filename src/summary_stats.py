import os
import pandas as pd

results_file = "data/evaluation_results.csv"

if not os.path.exists(results_file):
    print("No evaluation results file found yet.")
else:
    df = pd.read_csv(results_file)

    if df.empty:
        print("Evaluation results file is empty.")
    else:
        total_checked = len(df)
        avg_error = df["error"].mean()
        avg_abs_error = df["abs_error"].mean()

        direction_accuracy = None
        if "direction_correct" in df.columns:
            direction_accuracy = df["direction_correct"].mean() * 100

        print("Evaluation summary:")
        print(f"Total checked predictions: {total_checked}")
        print(f"Average error: {avg_error:.4f}")
        print(f"Average absolute error: {avg_abs_error:.4f}")

        if direction_accuracy is not None:
            print(f"Direction accuracy: {direction_accuracy:.2f}%")

        print("\nBy ticker:")
        by_ticker = df.groupby("ticker").agg(
            total_checked=("ticker", "count"),
            avg_error=("error", "mean"),
            avg_abs_error=("abs_error", "mean")
        )

        if "direction_correct" in df.columns:
            by_ticker["direction_accuracy_pct"] = df.groupby("ticker")["direction_correct"].mean() * 100

        print(by_ticker)