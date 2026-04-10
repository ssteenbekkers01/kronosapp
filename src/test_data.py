import yfinance as yf

ticker = "AAPL"

data = yf.download(
    ticker,
    period="3mo",
    interval="1d",
    auto_adjust=False,
    progress=False,
    threads=False
)

if data.empty:
    print("No data was downloaded.")
else:
    if hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
        data.columns = data.columns.get_level_values(0)

    data.columns.name = None

    print("Last 5 rows:")
    print(data.tail())

    data.to_csv("data/aapl_data.csv")
    print("Saved data to data/aapl_data.csv")