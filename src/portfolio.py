import sqlite3
from datetime import datetime

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


def add_ticker(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO portfolio (ticker, added_at) VALUES (?, ?)",
            (ticker.upper(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        print(f"{ticker} added")
    except:
        print(f"{ticker} already exists")

    conn.close()


def get_all_tickers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT ticker FROM portfolio")
    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]