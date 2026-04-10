from portfolio import create_table, add_ticker, get_all_tickers

create_table()

add_ticker("AAPL")
add_ticker("TSLA")
add_ticker("MSFT")

tickers = get_all_tickers()

print("Your portfolio:")
for t in tickers:
    print("-", t)