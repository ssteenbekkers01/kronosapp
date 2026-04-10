import io
from contextlib import redirect_stdout, redirect_stderr
import sqlite3
from datetime import datetime
import yfinance as yf

DB_PATH = "data/portfolio.db"


def create_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE,
            added_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def is_valid_yahoo_ticker(ticker):
    ticker = ticker.upper().strip()

    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            data = yf.download(
                ticker,
                period="5d",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False
            )
        return not data.empty
    except Exception:
        return False


def add_ticker(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    ticker = ticker.upper().strip()

    if not is_valid_yahoo_ticker(ticker):
        print(f"{ticker} is not a valid Yahoo Finance ticker")
        print("Use the exact Yahoo symbol, for example: RHM.DE")
        conn.close()
        return

    try:
        cursor.execute(
            "INSERT INTO portfolio (ticker, added_at) VALUES (?, ?)",
            (ticker, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        print(f"{ticker} added")
    except sqlite3.IntegrityError:
        print(f"{ticker} already exists")

    conn.close()


def get_all_tickers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT ticker FROM portfolio")
    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]