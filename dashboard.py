"""
EUR/USD VisionPulse AI - Streamlit Dashboard
Displays the latest chart photo, active sentiment, trade thesis,
performance stats, and a "Lessons Learned" log.
"""

import json
import time
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# --- Page Config ---
st.set_page_config(
    page_title="EUR/USD VisionPulse AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- File Paths ---
BASE_DIR = Path(__file__).parent
LATEST_ANALYSIS_FILE = BASE_DIR / "latest_analysis.json"
MEMORY_FILE = BASE_DIR / "memory.json"
CYCLE_LOG_FILE = BASE_DIR / "cycle_log.json"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"


def load_json(filepath: Path) -> dict | list | None:
    """Safely load a JSON file."""
    if filepath.exists():
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


# --- Sidebar ---
st.sidebar.title("⚙️ VisionPulse AI")
st.sidebar.markdown("**EUR/USD Trading Assistant**")

auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)
if auto_refresh:
    refresh_interval = st.sidebar.slider("Refresh interval (sec)", 10, 120, 30)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Actions")

if st.sidebar.button("🔄 Refresh Now"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **How it works:**
    1. Screenshots TradingView chart
    2. Fetches OHLCV data (yfinance)
    3. Pulls financial news headlines
    4. Gemini AI analyzes all data
    5. Records trades & learns from mistakes
    """
)

# --- Main Content ---
st.title("📊 EUR/USD VisionPulse AI")
st.caption(f"Last dashboard refresh: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

# Load data
latest = load_json(LATEST_ANALYSIS_FILE)
memory = load_json(MEMORY_FILE)

if latest is None:
    st.warning(
        "⚠️ No analysis data found. Run `python main.py --once` or `python main.py` first to generate analysis data."
    )
    st.stop()

analysis = latest.get("analysis", {})
updated_at = latest.get("updated_at", "N/A")

# --- Top Metrics Row ---
col1, col2, col3, col4 = st.columns(4)

thesis = analysis.get("trade_thesis", "N/A")
thesis_color = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "🟡"}.get(thesis, "⚪")
confidence = analysis.get("confidence_score", 0)
stats = latest.get("performance", {})

with col1:
    st.metric("Trade Thesis", f"{thesis_color} {thesis}")
with col2:
    st.metric("Confidence", f"{confidence:.1%}")
with col3:
    st.metric("Win Rate", f"{stats.get('win_rate', 0):.1f}%")
with col4:
    st.metric("Total Trades", stats.get("total_trades", 0))

st.markdown("---")

# --- Chart & Analysis Side by Side ---
chart_col, analysis_col = st.columns([1.2, 1])

with chart_col:
    st.subheader("📈 Latest Chart")
    chart_path = latest.get("chart_path")
    if chart_path and Path(chart_path).exists():
        st.image(chart_path, caption=f"Captured at {updated_at} UTC", use_container_width=True)
    else:
        # Try to find any screenshot
        screenshots = sorted(SCREENSHOTS_DIR.glob("eurusd_*.png")) if SCREENSHOTS_DIR.exists() else []
        if screenshots:
            st.image(str(screenshots[-1]), caption="Most recent screenshot", use_container_width=True)
        else:
            st.info("No chart screenshots available yet.")

with analysis_col:
    st.subheader("🧠 AI Analysis")

    if analysis.get("chart_analysis"):
        with st.expander("Chart Analysis", expanded=True):
            st.write(analysis["chart_analysis"])

    if analysis.get("technical_analysis"):
        with st.expander("Technical Analysis", expanded=True):
            st.write(analysis["technical_analysis"])

    if analysis.get("fundamental_analysis"):
        with st.expander("Fundamental Analysis", expanded=True):
            st.write(analysis["fundamental_analysis"])

    if analysis.get("reasoning"):
        with st.expander("Full Reasoning", expanded=False):
            st.write(analysis["reasoning"])

st.markdown("---")

# --- Trade Details ---
detail_col1, detail_col2 = st.columns(2)

with detail_col1:
    st.subheader("📍 Trade Levels")
    levels_data = {
        "Entry Price": analysis.get("entry_price", "N/A"),
        "Stop Loss": analysis.get("stop_loss", "N/A"),
        "Take Profit": analysis.get("take_profit", "N/A"),
        "Timeframe": analysis.get("timeframe", "N/A"),
    }
    for k, v in levels_data.items():
        st.write(f"**{k}:** {v}")

    key_levels = analysis.get("key_levels", {})
    if key_levels:
        st.write(f"**Support:** {key_levels.get('support', [])}")
        st.write(f"**Resistance:** {key_levels.get('resistance', [])}")

with detail_col2:
    st.subheader("⚠️ Risk Factors")
    risks = analysis.get("risk_factors", [])
    if risks:
        for risk in risks:
            st.write(f"- {risk}")
    else:
        st.write("No risk factors identified.")

st.markdown("---")

# --- Data Feeds ---
data_col1, data_col2 = st.columns(2)

with data_col1:
    st.subheader("📊 Quantitative Data")
    quant_text = latest.get("quant_text", "No data")
    st.code(quant_text, language=None)

with data_col2:
    st.subheader("📰 News Intelligence")
    news_text = latest.get("news_text", "No data")
    st.code(news_text, language=None)

st.markdown("---")

# --- Performance & Learning ---
perf_col, learn_col = st.columns(2)

with perf_col:
    st.subheader("📈 Performance Stats")
    if stats:
        perf_df = pd.DataFrame([{
            "Total Trades": stats.get("total_trades", 0),
            "Correct": stats.get("correct_predictions", 0),
            "Incorrect": stats.get("incorrect_predictions", 0),
            "Skipped": stats.get("neutral_skipped", 0),
            "Win Rate %": stats.get("win_rate", 0),
            "Avg Conf (Correct)": stats.get("avg_confidence_correct", 0),
            "Avg Conf (Incorrect)": stats.get("avg_confidence_incorrect", 0),
        }])
        st.dataframe(perf_df, use_container_width=True, hide_index=True)
    else:
        st.info("No performance data yet.")

with learn_col:
    st.subheader("🎓 Lessons Learned")
    lessons = latest.get("recent_lessons", [])
    if lessons:
        for i, lesson in enumerate(reversed(lessons), 1):
            st.write(f"**{i}.** {lesson}")
    else:
        st.info("No lessons yet. The AI will learn from its first closed trades.")

st.markdown("---")

# --- Trade History ---
st.subheader("📜 Trade History")
if memory and memory.get("trades"):
    trades = memory["trades"]
    trade_rows = []
    for t in reversed(trades[-20:]):
        trade_rows.append({
            "ID": t.get("trade_id", ""),
            "Status": t.get("status", ""),
            "Thesis": t.get("thesis", ""),
            "Confidence": f"{t.get('confidence', 0):.1%}",
            "Entry": t.get("entry_price", ""),
            "Exit": t.get("exit_price", ""),
            "PnL (pips)": t.get("pnl_pips", ""),
            "Outcome": t.get("actual_outcome", ""),
            "Opened": t.get("opened_at", "")[:19],
        })
    trade_df = pd.DataFrame(trade_rows)
    st.dataframe(trade_df, use_container_width=True, hide_index=True)
else:
    st.info("No trades recorded yet.")

# --- Cycle Log ---
with st.expander("🔄 Cycle Log (Recent Runs)"):
    cycle_log = load_json(CYCLE_LOG_FILE)
    if cycle_log:
        log_rows = []
        for entry in reversed(cycle_log[-20:]):
            log_rows.append({
                "Time": entry.get("cycle_start", "")[:19],
                "Status": entry.get("status", ""),
                "Thesis": entry.get("thesis", ""),
                "Confidence": entry.get("confidence", ""),
                "Duration (s)": entry.get("duration_seconds", ""),
                "News": entry.get("news_count", ""),
                "Trade": entry.get("trade_id", "-"),
            })
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No cycle log yet.")

# --- Footer ---
st.markdown("---")
st.caption(
    "**EUR/USD VisionPulse AI** | Simulated trading only — not financial advice. "
    "Built with Playwright, yfinance, Gemini AI, and Streamlit."
)

# --- Auto Refresh ---
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
