from data_fetcher import get_stock_data

ticker = "MSFT"
data = get_stock_data(ticker)

if data.empty:
    print("No data found.")
else:
    print(f"Downloaded data for {ticker}")
    print(data.tail())