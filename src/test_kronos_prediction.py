import sys
sys.path.append("Kronos")

import pandas as pd
from model import Kronos, KronosTokenizer, KronosPredictor

# Load saved stock data
data = pd.read_csv("data/AAPL.csv")

# Keep the columns Kronos needs
data = data[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
data.columns = ["timestamps", "open", "high", "low", "close", "volume"]
data["timestamps"] = pd.to_datetime(data["timestamps"])

# Use earlier rows as input, last row as target timestamp
lookback = len(data) - 1
pred_len = 1

x_df = data.loc[:lookback - 1, ["open", "high", "low", "close", "volume"]]
x_timestamp = data.loc[:lookback - 1, "timestamps"]
y_timestamp = data.loc[lookback:lookback + pred_len - 1, "timestamps"]

# Load Kronos
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")

predictor = KronosPredictor(
    model,
    tokenizer,
    device="cpu",
    max_context=512
)

# Make prediction
pred_df = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=pred_len,
    T=1.0,
    top_p=0.9,
    sample_count=1,
    verbose=True
)

# Save prediction
pred_df.to_csv("data/AAPL_prediction.csv")

print("Prediction result:")
print(pred_df)
print("\nSaved to data/AAPL_prediction.csv")