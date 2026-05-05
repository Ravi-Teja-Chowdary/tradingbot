"""
EUR/USD VisionPulse AI - Main Orchestrator
Runs the complete analysis cycle every 30 minutes:
1. Capture chart screenshot
2. Fetch OHLCV data
3. Fetch news headlines
4. Run multimodal AI analysis
5. Record trade & perform self-learning
"""

import json
import time
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from visual_perception import capture_chart_sync, get_latest_screenshot, cleanup_old_screenshots
from quantitative_data import fetch_ohlcv, get_current_price, format_data_for_prompt
from fundamental_intel import fetch_all_news, format_news_for_prompt
from multimodal_brain import analyze
from learning_loop import (
    record_trade,
    process_completed_trades,
    get_recent_lessons,
    get_performance_stats,
    get_open_trades,
)

# Store last analysis result for the dashboard to read
LATEST_ANALYSIS_FILE = Path(__file__).parent / "latest_analysis.json"
CYCLE_LOG_FILE = Path(__file__).parent / "cycle_log.json"

# Graceful shutdown flag
_shutdown = threading.Event()


def save_latest_analysis(analysis: dict, news_text: str, quant_text: str, chart_path: str | None):
    """Persist the latest analysis for the dashboard."""
    output = {
        "analysis": analysis,
        "news_text": news_text,
        "quant_text": quant_text,
        "chart_path": chart_path,
        "updated_at": datetime.utcnow().isoformat(),
        "performance": get_performance_stats(),
        "recent_lessons": get_recent_lessons(10),
    }
    with open(LATEST_ANALYSIS_FILE, "w") as f:
        json.dump(output, f, indent=2, default=str)


def append_cycle_log(entry: dict):
    """Append to the cycle log."""
    log = []
    if CYCLE_LOG_FILE.exists():
        try:
            with open(CYCLE_LOG_FILE, "r") as f:
                log = json.load(f)
        except (json.JSONDecodeError, IOError):
            log = []

    log.append(entry)
    # Keep last 200 entries
    log = log[-200:]

    with open(CYCLE_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2, default=str)


def run_analysis_cycle():
    """Execute one complete analysis cycle."""
    cycle_start = datetime.utcnow()
    print(f"\n{'='*60}")
    print(f"[Orchestrator] Starting analysis cycle at {cycle_start.isoformat()}")
    print(f"{'='*60}")

    log_entry = {
        "cycle_start": cycle_start.isoformat(),
        "status": "running",
    }

    # --- Step 1: Capture chart screenshot ---
    print("\n[Step 1/5] Capturing chart screenshot...")
    try:
        chart_path = capture_chart_sync()
        cleanup_old_screenshots(keep_last=48)
    except Exception as e:
        print(f"[Step 1] Screenshot capture failed: {e}")
        chart_path = get_latest_screenshot()
    log_entry["chart_path"] = chart_path

    # --- Step 2: Fetch OHLCV data ---
    print("\n[Step 2/5] Fetching OHLCV data...")
    try:
        df = fetch_ohlcv(period="5d", interval="30m")
        quant_text = format_data_for_prompt(df) if not df.empty else "Quantitative data unavailable."
    except Exception as e:
        print(f"[Step 2] OHLCV fetch failed: {e}")
        df = None
        quant_text = "Quantitative data unavailable."
    log_entry["has_quant_data"] = df is not None and not df.empty

    # --- Step 3: Fetch news ---
    print("\n[Step 3/5] Fetching news headlines...")
    try:
        articles = fetch_all_news(max_articles=20)
        news_text = format_news_for_prompt(articles) if articles else "No news data available."
    except Exception as e:
        print(f"[Step 3] News fetch failed: {e}")
        articles = []
        news_text = "No news data available."
    log_entry["news_count"] = len(articles)

    # --- Step 4: Self-learning - close old trades & learn ---
    print("\n[Step 4/5] Processing learning loop...")
    try:
        current = get_current_price()
        current_price = current.get("last_price")
        if current_price:
            process_completed_trades(current_price)
    except Exception as e:
        print(f"[Step 4] Learning loop error: {e}")
        current_price = None

    # Get accumulated lessons
    lessons = get_recent_lessons(10)

    # --- Step 5: AI Analysis ---
    print("\n[Step 5/5] Running multimodal AI analysis...")
    try:
        analysis = analyze(
            chart_image_path=chart_path,
            quant_text=quant_text,
            news_text=news_text,
            lessons_learned=lessons if lessons else None,
        )
    except Exception as e:
        print(f"[Step 5] AI analysis failed: {e}")
        analysis = {
            "trade_thesis": "NEUTRAL",
            "confidence_score": 0.0,
            "reasoning": f"Analysis failed: {e}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    log_entry["thesis"] = analysis.get("trade_thesis")
    log_entry["confidence"] = analysis.get("confidence_score")

    # --- Record simulated trade ---
    if analysis.get("trade_thesis") in ("BULLISH", "BEARISH"):
        confidence = analysis.get("confidence_score", 0)
        if confidence >= 0.4:
            entry_price = analysis.get("entry_price") or current_price
            if entry_price:
                trade_id = record_trade(analysis, entry_price=entry_price)
                log_entry["trade_id"] = trade_id
                print(f"\n[Trade] Opened simulated trade: {trade_id}")
            else:
                print("\n[Trade] Skipped: No entry price available.")
        else:
            print(f"\n[Trade] Skipped: Confidence {confidence:.1%} below threshold.")
    else:
        print(f"\n[Trade] Skipped: Thesis is NEUTRAL.")

    # --- Save results ---
    save_latest_analysis(analysis, news_text, quant_text, chart_path)

    cycle_end = datetime.utcnow()
    duration = (cycle_end - cycle_start).total_seconds()
    log_entry["cycle_end"] = cycle_end.isoformat()
    log_entry["duration_seconds"] = round(duration, 1)
    log_entry["status"] = "completed"
    append_cycle_log(log_entry)

    # --- Print summary ---
    print(f"\n{'='*60}")
    print(f"[Orchestrator] Cycle completed in {duration:.1f}s")
    print(f"  Thesis: {analysis.get('trade_thesis')} | Confidence: {analysis.get('confidence_score', 0):.1%}")
    print(f"  Open Trades: {len(get_open_trades())}")
    stats = get_performance_stats()
    print(f"  Win Rate: {stats.get('win_rate', 0)}% ({stats.get('total_trades', 0)} total trades)")
    if lessons:
        print(f"  Active Lessons: {len(lessons)}")
    print(f"{'='*60}\n")

    return analysis


def run_loop(interval_minutes: int = 30):
    """Run the analysis cycle in a loop."""
    print(f"[VisionPulse AI] Starting loop (interval: {interval_minutes} min)")
    print(f"[VisionPulse AI] Press Ctrl+C to stop\n")

    # Run first cycle immediately
    run_analysis_cycle()

    while not _shutdown.is_set():
        print(f"[VisionPulse AI] Next cycle in {interval_minutes} minutes...")
        # Wait in small increments to allow graceful shutdown
        for _ in range(interval_minutes * 60):
            if _shutdown.is_set():
                break
            time.sleep(1)

        if not _shutdown.is_set():
            run_analysis_cycle()

    print("[VisionPulse AI] Shutdown complete.")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n[VisionPulse AI] Shutting down gracefully...")
    _shutdown.set()


def main():
    signal.signal(signal.SIGINT, signal_handler)

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single run mode
        result = run_analysis_cycle()
        print(json.dumps(result, indent=2, default=str))
    else:
        # Continuous loop mode
        interval = 30
        if len(sys.argv) > 1:
            try:
                interval = int(sys.argv[1])
            except ValueError:
                pass
        run_loop(interval_minutes=interval)


if __name__ == "__main__":
    main()
