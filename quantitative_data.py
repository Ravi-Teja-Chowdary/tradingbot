"""
EUR/USD VisionPulse AI - Quantitative Data Layer
Fetches real-time OHLCV data for EUR/USD using yfinance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime


# yfinance ticker for EUR/USD
EURUSD_TICKER = "EURUSD=X"


def fetch_ohlcv(period: str = "5d", interval: str = "30m") -> pd.DataFrame:
    """
    Fetch OHLCV data for EUR/USD.

    Args:
        period: Data period (e.g., '1d', '5d', '1mo')
        interval: Data interval (e.g., '1m', '5m', '15m', '30m', '1h', '1d')

    Returns:
        DataFrame with Open, High, Low, Close, Volume columns.
    """
    try:
        ticker = yf.Ticker(EURUSD_TICKER)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            print("[QuantData] Warning: No data returned from yfinance.")
            return pd.DataFrame()

        # Keep only relevant columns
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index.name = "Datetime"

        print(f"[QuantData] Fetched {len(df)} candles ({interval} interval, {period} period)")
        return df

    except Exception as e:
        print(f"[QuantData] Error fetching data: {e}")
        return pd.DataFrame()


def get_current_price() -> dict:
    """
    Get the latest EUR/USD price data.

    Returns:
        Dictionary with current price info.
    """
    try:
        ticker = yf.Ticker(EURUSD_TICKER)
        info = ticker.fast_info

        current = {
            "last_price": round(float(info.last_price), 5) if hasattr(info, "last_price") else None,
            "previous_close": round(float(info.previous_close), 5) if hasattr(info, "previous_close") else None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Compute change
        if current["last_price"] and current["previous_close"]:
            change = current["last_price"] - current["previous_close"]
            current["change"] = round(change, 5)
            current["change_pct"] = round((change / current["previous_close"]) * 100, 4)

        print(f"[QuantData] Current EUR/USD: {current.get('last_price', 'N/A')}")
        return current

    except Exception as e:
        print(f"[QuantData] Error fetching current price: {e}")
        return {"last_price": None, "timestamp": datetime.utcnow().isoformat(), "error": str(e)}


def get_technical_summary(df: pd.DataFrame) -> dict:
    """
    Compute basic technical indicators from OHLCV data.

    Returns:
        Dictionary with SMA, RSI, ATR, and recent candle patterns.
    """
    if df.empty or len(df) < 14:
        return {"error": "Insufficient data for technical analysis"}

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # Simple Moving Averages
    sma_10 = round(float(close.rolling(10).mean().iloc[-1]), 5)
    sma_20 = round(float(close.rolling(20).mean().iloc[-1]), 5)

    # RSI (14-period)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_value = round(float(rsi.iloc[-1]), 2)

    # ATR (14-period)
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    atr = round(float(tr.rolling(14).mean().iloc[-1]), 5)

    # Recent candles summary
    last_5 = df.tail(5)
    candle_summary = []
    for idx, row in last_5.iterrows():
        direction = "Bullish" if row["Close"] > row["Open"] else "Bearish"
        body = abs(row["Close"] - row["Open"])
        candle_summary.append({
            "time": str(idx),
            "direction": direction,
            "open": round(float(row["Open"]), 5),
            "high": round(float(row["High"]), 5),
            "low": round(float(row["Low"]), 5),
            "close": round(float(row["Close"]), 5),
            "body_size": round(float(body), 5),
        })

    latest_close = round(float(close.iloc[-1]), 5)

    summary = {
        "latest_close": latest_close,
        "sma_10": sma_10,
        "sma_20": sma_20,
        "sma_signal": "Bullish" if sma_10 > sma_20 else "Bearish",
        "rsi_14": rsi_value,
        "rsi_signal": "Overbought" if rsi_value > 70 else ("Oversold" if rsi_value < 30 else "Neutral"),
        "atr_14": atr,
        "last_5_candles": candle_summary,
    }

    print(f"[QuantData] Technical Summary - SMA: {summary['sma_signal']}, RSI: {rsi_value}, ATR: {atr}")
    return summary


def format_data_for_prompt(df: pd.DataFrame) -> str:
    """Format OHLCV data and technicals as a text prompt for the AI."""
    current = get_current_price()
    technicals = get_technical_summary(df)

    lines = [
        "=== EUR/USD QUANTITATIVE DATA ===",
        f"Current Price: {current.get('last_price', 'N/A')}",
        f"Previous Close: {current.get('previous_close', 'N/A')}",
        f"Change: {current.get('change', 'N/A')} ({current.get('change_pct', 'N/A')}%)",
        "",
        "--- Technical Indicators ---",
        f"SMA(10): {technicals.get('sma_10', 'N/A')}",
        f"SMA(20): {technicals.get('sma_20', 'N/A')}",
        f"SMA Signal: {technicals.get('sma_signal', 'N/A')}",
        f"RSI(14): {technicals.get('rsi_14', 'N/A')} ({technicals.get('rsi_signal', 'N/A')})",
        f"ATR(14): {technicals.get('atr_14', 'N/A')}",
        "",
        "--- Last 5 Candles (30m) ---",
    ]

    for c in technicals.get("last_5_candles", []):
        lines.append(
            f"  {c['time']}: {c['direction']} | O:{c['open']} H:{c['high']} L:{c['low']} C:{c['close']}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    df = fetch_ohlcv()
    if not df.empty:
        print(format_data_for_prompt(df))
