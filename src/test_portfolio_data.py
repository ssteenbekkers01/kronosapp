from portfolio import get_all_tickers
from data_fetcher import get_stock_data

tickers = get_all_tickers()

if not tickers:
    print("Your portfolio is empty.")
else:
    print("Your portfolio:")
    for ticker in tickers:
        print("-", ticker)

    print("\nDownloading data...\n")

    for ticker in tickers:
        data = get_stock_data(ticker)

        if data.empty:
            print(f"{ticker}: no data found")
        else:
            file_path = f"data/{ticker}.csv"
            data.to_csv(file_path)

            print(f"{ticker}: {len(data)} rows downloaded")
            print(f"Saved to {file_path}")
            print(data.tail(2))
            print()