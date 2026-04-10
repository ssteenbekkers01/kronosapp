import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Kronos Dashboard", layout="wide")

DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "predictions.db")

st.title("Kronos Stock Prediction Dashboard")


@st.cache_data
def load_predictions_from_db():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()

    conn = sqlite3.connect(DB_FILE)

    query = """
    SELECT ticker, timestamps, open, high, low, close, run_timestamp
    FROM predictions
    ORDER BY run_timestamp DESC, ticker ASC, timestamps ASC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        for col in ["timestamps", "run_timestamp"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


@st.cache_data
def load_evaluations_from_db():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()

    conn = sqlite3.connect(DB_FILE)

    try:
        query = """
        SELECT
            ticker,
            prediction_date,
            direction_correct,
            abs_error,
            predicted_return,
            actual_return,
            run_timestamp
        FROM evaluations
        """
        df = pd.read_sql_query(query, conn)
    except Exception:
        conn.close()
        return pd.DataFrame()

    conn.close()

    if not df.empty:
        for col in ["prediction_date", "run_timestamp"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


@st.cache_data
def load_price_data(ticker):
    file_path = os.path.join(DATA_DIR, f"{ticker}.csv")

    if not os.path.exists(file_path):
        return pd.DataFrame(), None

    try:
        df = pd.read_csv(file_path)
        df.columns = [col.lower() for col in df.columns]

        date_col = None
        for col in ["date", "datetime", "timestamp"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                date_col = col
                break

        return df, date_col

    except Exception as e:
        st.error(f"Could not read {ticker}.csv: {e}")
        return pd.DataFrame(), None


def format_timestamp(ts):
    if pd.isna(ts):
        return "Unknown"
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def make_candlestick_chart(hist_df, hist_date_col, pred_df, ticker):
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=hist_df[hist_date_col],
            open=hist_df["open"],
            high=hist_df["high"],
            low=hist_df["low"],
            close=hist_df["close"],
            name="Historical",
            increasing_line_color="#00cc96",
            decreasing_line_color="#ef553b",
        )
    )

    if not pred_df.empty:
        fig.add_trace(
            go.Candlestick(
                x=pred_df["timestamps"],
                open=pred_df["open"],
                high=pred_df["high"],
                low=pred_df["low"],
                close=pred_df["close"],
                name="Predicted",
                increasing_line_color="#636efa",
                decreasing_line_color="#ffa15a",
            )
        )

        forecast_start = pred_df["timestamps"].min()
        if pd.notna(forecast_start):
            fig.add_vline(
                x=forecast_start,
                line_width=2,
                line_dash="dash",
                line_color="gray",
            )

    fig.update_layout(
        title=f"{ticker} — 20 Historical Days + 10 Predicted Days",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=650,
        legend_title="Data Type",
    )

    return fig


def build_best_signals_table(pred_df, eval_df):
    if pred_df.empty or "ticker" not in pred_df.columns:
        return pd.DataFrame()

    signal_rows = []

    for ticker in sorted(pred_df["ticker"].dropna().unique()):
        ticker_pred = pred_df[pred_df["ticker"] == ticker].copy()

        if ticker_pred.empty:
            continue

        ticker_pred = ticker_pred.sort_values(["run_timestamp", "timestamps"])

        latest_run = ticker_pred["run_timestamp"].max()
        latest_pred = ticker_pred[ticker_pred["run_timestamp"] == latest_run].copy()

        if latest_pred.empty:
            continue

        latest_pred = latest_pred.sort_values("timestamps")

        price_df, price_date_col = load_price_data(ticker)
        if price_df.empty or not price_date_col or "close" not in price_df.columns:
            continue

        price_df = price_df.sort_values(price_date_col)
        hist_df = price_df[[price_date_col, "close"]].dropna()

        if hist_df.empty:
            continue

        latest_actual_close = hist_df["close"].iloc[-1]
        first_pred_close = latest_pred["close"].iloc[0]
        final_pred_close = latest_pred["close"].iloc[-1]

        expected_return_pct = ((final_pred_close - latest_actual_close) / latest_actual_close) * 100

        ticker_eval = eval_df[eval_df["ticker"] == ticker].copy() if not eval_df.empty else pd.DataFrame()

        if not ticker_eval.empty:
            direction_accuracy = ticker_eval["direction_correct"].astype(float).mean() * 100
            avg_abs_error = ticker_eval["abs_error"].astype(float).mean()

            if "actual_return" in ticker_eval.columns:
                avg_actual_return = ticker_eval["actual_return"].astype(float).mean() * 100
            else:
                avg_actual_return = None
        else:
            direction_accuracy = None
            avg_abs_error = None
            avg_actual_return = None

        score = expected_return_pct

        if direction_accuracy is not None:
            score += (direction_accuracy - 50) * 0.2

        if avg_actual_return is not None:
            score += avg_actual_return * 0.5

        if avg_abs_error is not None:
            score -= avg_abs_error * 0.1

        if score >= 8:
            signal = "Strong Buy"
        elif score >= 2:
            signal = "Buy"
        elif score <= -8:
            signal = "Strong Sell"
        elif score <= -2:
            signal = "Sell"
        else:
            signal = "Hold"

        signal_rows.append({
            "ticker": ticker,
            "latest_actual_close": round(latest_actual_close, 2),
            "first_pred_close": round(first_pred_close, 2),
            "final_pred_close": round(final_pred_close, 2),
            "expected_return_pct": round(expected_return_pct, 2),
            "direction_accuracy_pct": round(direction_accuracy, 2) if direction_accuracy is not None else None,
            "avg_actual_return_pct": round(avg_actual_return, 2) if avg_actual_return is not None else None,
            "avg_abs_error": round(avg_abs_error, 2) if avg_abs_error is not None else None,
            "score": round(score, 2),
            "signal": signal,
        })

    if not signal_rows:
        return pd.DataFrame()

    signals_df = pd.DataFrame(signal_rows)
    signals_df = signals_df.sort_values("score", ascending=False).reset_index(drop=True)
    return signals_df

def build_performance_summary(eval_df):
    if eval_df.empty:
        return {
            "evaluated_rows": 0,
            "win_rate_pct": None,
            "avg_predicted_return_pct": None,
            "avg_actual_return_pct": None,
            "avg_error_pct": None,
            "return_gap_pct": None,
        }

    summary = {
        "evaluated_rows": len(eval_df),
        "win_rate_pct": None,
        "avg_predicted_return_pct": None,
        "avg_actual_return_pct": None,
        "avg_error_pct": None,
        "return_gap_pct": None,
    }

    if "direction_correct" in eval_df.columns:
        summary["win_rate_pct"] = eval_df["direction_correct"].astype(float).mean() * 100

    if "predicted_return" in eval_df.columns:
        summary["avg_predicted_return_pct"] = eval_df["predicted_return"].astype(float).mean() * 100

    if "actual_return" in eval_df.columns:
        summary["avg_actual_return_pct"] = eval_df["actual_return"].astype(float).mean() * 100

    if (
        summary["avg_actual_return_pct"] is not None
        and summary["avg_predicted_return_pct"] is not None
    ):
        summary["return_gap_pct"] = (
            summary["avg_actual_return_pct"] - summary["avg_predicted_return_pct"]
        )

    if "error_pct" in eval_df.columns:
        summary["avg_error_pct"] = eval_df["error_pct"].astype(float).mean() * 100

    return summary

pred_df = load_predictions_from_db()
eval_df = load_evaluations_from_db()
performance = build_performance_summary(eval_df)

if pred_df.empty:
    st.warning("No prediction data found in data/predictions.db yet.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Prediction Rows", len(pred_df))

with col2:
    if "ticker" in pred_df.columns:
        st.metric("Tickers", pred_df["ticker"].nunique())
    else:
        st.metric("Tickers", 0)

with col3:
    if "run_timestamp" in pred_df.columns and pred_df["run_timestamp"].notna().any():
        last_updated = pred_df["run_timestamp"].max()
        st.metric("Last Updated", format_timestamp(last_updated))
    else:
        st.metric("Last Updated", "Unknown")

with col4:
    st.metric("Evaluated Rows", len(eval_df))

st.subheader("Performance Summary")

p1, p2, p3, p4, p5 = st.columns(5)

with p1:
    st.metric("Evaluated Predictions", performance["evaluated_rows"])

with p2:
    st.metric(
        "Win Rate",
        f"{performance['win_rate_pct']:.1f}%"
        if performance["win_rate_pct"] is not None else "N/A"
    )

with p3:
    st.metric(
        "Avg Predicted Return",
        f"{performance['avg_predicted_return_pct']:.2f}%"
        if performance["avg_predicted_return_pct"] is not None else "N/A"
    )

with p4:
    st.metric(
        "Avg Actual Return",
        f"{performance['avg_actual_return_pct']:.2f}%"
        if performance["avg_actual_return_pct"] is not None else "N/A"
    )

with p5:
    st.metric(
        "Return Gap",
        f"{performance['return_gap_pct']:.2f}%"
        if performance["return_gap_pct"] is not None else "N/A"
    )

st.caption(
    f"Avg Prediction Error: {performance['avg_error_pct']:.2f}%"
    if performance["avg_error_pct"] is not None else "Avg Prediction Error: N/A"
)

st.divider()

st.divider()

st.subheader("Best Current Signals")
signals_df = build_best_signals_table(pred_df, eval_df)

if signals_df.empty:
    st.info("No signals could be calculated yet.")
else:
    st.dataframe(signals_df, use_container_width=True)

st.divider()

if "ticker" not in pred_df.columns:
    st.error("The predictions table does not contain a 'ticker' column.")
    st.stop()

tickers = sorted(pred_df["ticker"].dropna().unique().tolist())
selected_ticker = st.selectbox("Select ticker", tickers)

ticker_pred_df = pred_df[pred_df["ticker"] == selected_ticker].copy()

if "run_timestamp" in ticker_pred_df.columns and ticker_pred_df["run_timestamp"].notna().any():
    latest_run = ticker_pred_df["run_timestamp"].max()
    ticker_pred_df = ticker_pred_df[ticker_pred_df["run_timestamp"] == latest_run].copy()

if "timestamps" in ticker_pred_df.columns:
    ticker_pred_df = ticker_pred_df.sort_values("timestamps")

price_df, price_date_col = load_price_data(selected_ticker)

st.subheader(f"{selected_ticker} Price Forecast Chart")

if price_df.empty or not price_date_col:
    st.warning(f"No usable historical price data found for {selected_ticker}.")
else:
    required_hist_cols = ["open", "high", "low", "close"]
    required_pred_cols = ["timestamps", "open", "high", "low", "close"]

    missing_hist = [col for col in required_hist_cols if col not in price_df.columns]
    missing_pred = [col for col in required_pred_cols if col not in ticker_pred_df.columns]

    if missing_hist:
        st.warning(f"{selected_ticker}.csv is missing columns: {missing_hist}")
    elif missing_pred:
        st.warning(f"Prediction data is missing columns: {missing_pred}")
    else:
        price_df = price_df.sort_values(price_date_col)
        hist_df = price_df[[price_date_col, "open", "high", "low", "close"]].dropna().tail(20).copy()
        future_df = ticker_pred_df[["timestamps", "open", "high", "low", "close"]].dropna().head(10).copy()

        if hist_df.empty:
            st.warning("Historical data is empty after cleaning.")
        elif future_df.empty:
            st.warning("Predicted data is empty after cleaning.")
        else:
            fig = make_candlestick_chart(hist_df, price_date_col, future_df, selected_ticker)
            st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader(f"{selected_ticker} Latest Predicted OHLC Data")
st.dataframe(ticker_pred_df, use_container_width=True)

st.divider()

with st.expander("Debug / Columns Found"):
    st.write("Prediction columns:", pred_df.columns.tolist())
    st.write("Evaluation columns:", eval_df.columns.tolist() if not eval_df.empty else [])
    if not price_df.empty:
        st.write("Historical columns:", price_df.columns.tolist())