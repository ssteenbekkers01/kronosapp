import sys
sys.path.append("Kronos")

import pandas as pd
from model import Kronos, KronosTokenizer, KronosPredictor
from portfolio import get_all_tickers

# Load Kronos once
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")

predictor = KronosPredictor(
    model,
    tokenizer,
    device="cpu",
    max_context=512
)

tickers = get_all_tickers()
all_predictions = []

if not tickers:
    print("Your portfolio is empty.")
else:
    for ticker in tickers:
        file_path = f"data/{ticker}.csv"

        try:
            data = pd.read_csv(file_path)
            data = data.dropna(subset=["Date", "Open", "High", "Low", "Close", "Volume"])
        except FileNotFoundError:
            print(f"{ticker}: file not found")
            continue

        if len(data) < 30:
            print(f"{ticker}: not enough data")
            continue

        # Keep only the columns Kronos needs
        data = data[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
        data.columns = ["timestamps", "open", "high", "low", "close", "volume"]
        data["timestamps"] = pd.to_datetime(data["timestamps"])

        # Use all historical rows as input
        x_df = data[["open", "high", "low", "close", "volume"]].copy()
        x_timestamp = data["timestamps"].copy()

        # Predict 10 future trading days
        pred_len = 10
        last_date = x_timestamp.iloc[-1]

        # Create 10 future business days after the last real date
        future_dates = pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=pred_len)
        y_timestamp = pd.Series(future_dates)

        # Run Kronos
        pred_df = predictor.predict(
            df=x_df,
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=pred_len,
            T=1.0,
            top_p=0.9,
            sample_count=1,
            verbose=False
        )

        # Turn prediction output into rows we can save
        pred_df = pred_df.reset_index()

        # Make sure the date column is called "timestamps"
        if "index" in pred_df.columns:
            pred_df = pred_df.rename(columns={"index": "timestamps"})
        elif "Date" in pred_df.columns:
            pred_df = pred_df.rename(columns={"Date": "timestamps"})

        pred_df["ticker"] = ticker

        all_predictions.append(pred_df)
        print(f"{ticker}: 10-day prediction done")

if all_predictions:
    result_df = pd.concat(all_predictions, ignore_index=True)

    print("\nColumns found:")
    print(result_df.columns.tolist())

    # Fix column naming if needed
    if "index" in result_df.columns:
        result_df = result_df.rename(columns={"index": "timestamps"})
    elif "Date" in result_df.columns:
        result_df = result_df.rename(columns={"Date": "timestamps"})

    # Put columns in a nice order
    result_df = result_df[["ticker", "timestamps", "open", "high", "low", "close", "volume", "amount"]]

    result_df.to_csv("data/all_predictions.csv", index=False)

    print("\nSaved to data/all_predictions.csv")
    print(result_df.head(15))
else:
    print("No predictions were created.")
    