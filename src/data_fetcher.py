import yfinance as yf


def get_stock_data(ticker, period="3mo", interval="1d"):
    data = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False
    )

    if data.empty:
        return data

    if hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
        data.columns = data.columns.get_level_values(0)

    data.columns.name = None

    return data