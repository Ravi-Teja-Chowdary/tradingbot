"""
EUR/USD VisionPulse AI - Self-Learning Loop
Manages memory.json database. After each simulated trade, performs a Post-Mortem
analysis comparing predictions to actual outcomes, identifies failure reasons,
and updates strategy for the next run.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "memory.json"

DEFAULT_MEMORY = {
    "version": "1.0",
    "created_at": datetime.utcnow().isoformat(),
    "trades": [],
    "lessons_learned": [],
    "strategy_adjustments": [],
    "performance_stats": {
        "total_trades": 0,
        "correct_predictions": 0,
        "incorrect_predictions": 0,
        "neutral_skipped": 0,
        "win_rate": 0.0,
        "avg_confidence_correct": 0.0,
        "avg_confidence_incorrect": 0.0,
    },
}


def _load_memory() -> dict:
    """Load or initialize the memory database."""
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("[LearningLoop] Corrupted memory.json, reinitializing.")
    return DEFAULT_MEMORY.copy()


def _save_memory(memory: dict):
    """Save the memory database to disk."""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2, default=str)


def record_trade(analysis: dict, entry_price: float | None = None) -> str:
    """
    Record a new simulated trade based on AI analysis.

    Args:
        analysis: The full analysis dict from the multimodal brain.
        entry_price: Override entry price (uses analysis entry_price if None).

    Returns:
        The trade_id of the recorded trade.
    """
    memory = _load_memory()

    trade_id = f"trade_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    price = entry_price or analysis.get("entry_price")

    trade = {
        "trade_id": trade_id,
        "opened_at": datetime.utcnow().isoformat(),
        "closed_at": None,
        "status": "OPEN",
        "thesis": analysis.get("trade_thesis", "NEUTRAL"),
        "confidence": analysis.get("confidence_score", 0.0),
        "entry_price": price,
        "stop_loss": analysis.get("stop_loss"),
        "take_profit": analysis.get("take_profit"),
        "exit_price": None,
        "actual_outcome": None,
        "pnl_pips": None,
        "reasoning": analysis.get("reasoning", ""),
        "chart_analysis": analysis.get("chart_analysis", ""),
        "risk_factors": analysis.get("risk_factors", []),
        "post_mortem": None,
    }

    memory["trades"].append(trade)
    _save_memory(memory)
    print(f"[LearningLoop] Trade recorded: {trade_id} | {trade['thesis']} @ {price}")
    return trade_id


def close_trade(trade_id: str, exit_price: float) -> dict | None:
    """
    Close a trade and determine the actual outcome.

    Args:
        trade_id: The ID of the trade to close.
        exit_price: The closing price.

    Returns:
        The closed trade dict, or None if not found.
    """
    memory = _load_memory()

    for trade in memory["trades"]:
        if trade["trade_id"] == trade_id and trade["status"] == "OPEN":
            trade["closed_at"] = datetime.utcnow().isoformat()
            trade["exit_price"] = exit_price
            trade["status"] = "CLOSED"

            if trade["entry_price"] is not None:
                pnl = exit_price - trade["entry_price"]
                trade["pnl_pips"] = round(pnl * 10000, 1)  # Forex pip calculation

                # Determine if prediction was correct
                if trade["thesis"] == "BULLISH":
                    trade["actual_outcome"] = "CORRECT" if pnl > 0 else "INCORRECT"
                elif trade["thesis"] == "BEARISH":
                    trade["actual_outcome"] = "CORRECT" if pnl < 0 else "INCORRECT"
                else:
                    trade["actual_outcome"] = "NEUTRAL_SKIP"
            else:
                trade["actual_outcome"] = "NO_ENTRY_PRICE"

            _save_memory(memory)
            print(f"[LearningLoop] Trade closed: {trade_id} | Outcome: {trade['actual_outcome']} | PnL: {trade.get('pnl_pips')} pips")
            return trade

    print(f"[LearningLoop] Trade not found or already closed: {trade_id}")
    return None


def auto_close_old_trades(current_price: float, max_age_hours: int = 1):
    """
    Auto-close trades older than max_age_hours using the current price.
    This simulates trade exits for the learning loop.
    """
    memory = _load_memory()
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

    closed_count = 0
    for trade in memory["trades"]:
        if trade["status"] == "OPEN":
            opened = datetime.fromisoformat(trade["opened_at"])
            if opened < cutoff:
                trade["closed_at"] = datetime.utcnow().isoformat()
                trade["exit_price"] = current_price
                trade["status"] = "CLOSED"

                if trade["entry_price"] is not None:
                    pnl = current_price - trade["entry_price"]
                    trade["pnl_pips"] = round(pnl * 10000, 1)

                    if trade["thesis"] == "BULLISH":
                        trade["actual_outcome"] = "CORRECT" if pnl > 0 else "INCORRECT"
                    elif trade["thesis"] == "BEARISH":
                        trade["actual_outcome"] = "CORRECT" if pnl < 0 else "INCORRECT"
                    else:
                        trade["actual_outcome"] = "NEUTRAL_SKIP"
                else:
                    trade["actual_outcome"] = "NO_ENTRY_PRICE"

                closed_count += 1

    if closed_count > 0:
        _save_memory(memory)
        print(f"[LearningLoop] Auto-closed {closed_count} expired trade(s)")


def perform_post_mortem(trade_id: str) -> dict | None:
    """
    Perform a post-mortem analysis on a closed trade.
    Compares prediction vs actual, identifies failure reasons.

    Returns:
        Post-mortem analysis dict.
    """
    memory = _load_memory()

    for trade in memory["trades"]:
        if trade["trade_id"] == trade_id and trade["status"] == "CLOSED":
            if trade["post_mortem"] is not None:
                return trade["post_mortem"]

            post_mortem = {
                "analyzed_at": datetime.utcnow().isoformat(),
                "prediction": trade["thesis"],
                "outcome": trade["actual_outcome"],
                "confidence_was": trade["confidence"],
                "pnl_pips": trade["pnl_pips"],
            }

            if trade["actual_outcome"] == "INCORRECT":
                # Identify likely failure reasons
                failure_reasons = _identify_failure_reasons(trade)
                post_mortem["failure_reasons"] = failure_reasons
                post_mortem["lesson"] = _generate_lesson(trade, failure_reasons)

                # Record the lesson
                if post_mortem["lesson"]:
                    memory["lessons_learned"].append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "trade_id": trade_id,
                        "lesson": post_mortem["lesson"],
                    })

                    # Keep only last 50 lessons
                    memory["lessons_learned"] = memory["lessons_learned"][-50:]

            elif trade["actual_outcome"] == "CORRECT":
                post_mortem["success_note"] = "Prediction was correct. Reinforcing current strategy."

            trade["post_mortem"] = post_mortem
            _update_performance_stats(memory)
            _save_memory(memory)

            print(f"[LearningLoop] Post-mortem complete for {trade_id}: {trade['actual_outcome']}")
            return post_mortem

    return None


def _identify_failure_reasons(trade: dict) -> list[str]:
    """Identify potential reasons for a trade prediction failure."""
    reasons = []

    # High confidence but wrong
    if trade["confidence"] > 0.7:
        reasons.append("Overconfidence: High confidence score but wrong prediction")

    # Check if risk factors materialized
    if trade["risk_factors"]:
        reasons.append(f"Risk factors may have materialized: {', '.join(trade['risk_factors'][:3])}")

    # Check for fundamental news miss
    chart_text = trade.get("chart_analysis", "").lower()
    if any(kw in chart_text for kw in ["nfp", "cpi", "fomc", "ecb", "fed"]):
        reasons.append("Possible fundamental news impact was underweighted")

    # Direction reversal
    if trade["thesis"] == "BULLISH" and (trade.get("pnl_pips") or 0) < -10:
        reasons.append("Strong reversal against bullish thesis - possible trend change missed")
    elif trade["thesis"] == "BEARISH" and (trade.get("pnl_pips") or 0) > 10:
        reasons.append("Strong reversal against bearish thesis - possible trend change missed")

    # Low confidence trade
    if trade["confidence"] < 0.4:
        reasons.append("Low confidence trade should have been skipped (NEUTRAL)")

    if not reasons:
        reasons.append("Unknown - trade went against prediction with no clear pattern")

    return reasons


def _generate_lesson(trade: dict, failure_reasons: list[str]) -> str:
    """Generate a concise lesson from a failed trade."""
    thesis = trade["thesis"]
    pnl = trade.get("pnl_pips", 0)
    confidence = trade["confidence"]

    primary_reason = failure_reasons[0] if failure_reasons else "unknown reason"

    lesson = (
        f"[{trade['trade_id']}] Predicted {thesis} with confidence {confidence:.1%}, "
        f"but lost {abs(pnl or 0):.1f} pips. Primary issue: {primary_reason}. "
        f"Adjustment: "
    )

    if "Overconfidence" in primary_reason:
        lesson += "Reduce confidence when signals are marginally aligned."
    elif "fundamental" in primary_reason.lower() or "news" in primary_reason.lower():
        lesson += "Give more weight to fundamental news events, especially high-impact releases."
    elif "reversal" in primary_reason.lower():
        lesson += "Look for reversal signals and validate trend strength before committing."
    elif "Low confidence" in primary_reason:
        lesson += "Skip trades below 0.4 confidence threshold."
    else:
        lesson += "Review alignment between chart patterns, technicals, and fundamentals."

    return lesson


def _update_performance_stats(memory: dict):
    """Update aggregate performance statistics."""
    trades = [t for t in memory["trades"] if t["status"] == "CLOSED"]

    if not trades:
        return

    correct = [t for t in trades if t["actual_outcome"] == "CORRECT"]
    incorrect = [t for t in trades if t["actual_outcome"] == "INCORRECT"]
    neutral = [t for t in trades if t["actual_outcome"] == "NEUTRAL_SKIP"]

    total = len(correct) + len(incorrect)

    memory["performance_stats"] = {
        "total_trades": len(trades),
        "correct_predictions": len(correct),
        "incorrect_predictions": len(incorrect),
        "neutral_skipped": len(neutral),
        "win_rate": round(len(correct) / total * 100, 1) if total > 0 else 0.0,
        "avg_confidence_correct": round(
            sum(t["confidence"] for t in correct) / len(correct), 3
        ) if correct else 0.0,
        "avg_confidence_incorrect": round(
            sum(t["confidence"] for t in incorrect) / len(incorrect), 3
        ) if incorrect else 0.0,
    }


def get_recent_lessons(n: int = 10) -> list[str]:
    """Get the N most recent lessons learned."""
    memory = _load_memory()
    lessons = memory.get("lessons_learned", [])
    return [l["lesson"] for l in lessons[-n:]]


def get_performance_stats() -> dict:
    """Get current performance statistics."""
    memory = _load_memory()
    return memory.get("performance_stats", DEFAULT_MEMORY["performance_stats"])


def get_open_trades() -> list[dict]:
    """Get all currently open trades."""
    memory = _load_memory()
    return [t for t in memory["trades"] if t["status"] == "OPEN"]


def get_trade_history(n: int = 20) -> list[dict]:
    """Get the N most recent trades."""
    memory = _load_memory()
    return memory["trades"][-n:]


def get_strategy_adjustments() -> list[str]:
    """Get the current list of strategy adjustments derived from lessons."""
    memory = _load_memory()
    return [l["lesson"] for l in memory.get("lessons_learned", [])[-10:]]


def process_completed_trades(current_price: float):
    """
    Full learning cycle: auto-close expired trades, run post-mortems.
    """
    # Auto-close old trades
    auto_close_old_trades(current_price, max_age_hours=1)

    # Run post-mortems on closed trades without one
    memory = _load_memory()
    for trade in memory["trades"]:
        if trade["status"] == "CLOSED" and trade["post_mortem"] is None:
            perform_post_mortem(trade["trade_id"])


if __name__ == "__main__":
    # Demo: create a trade, close it, and run post-mortem
    demo_analysis = {
        "trade_thesis": "BULLISH",
        "confidence_score": 0.72,
        "entry_price": 1.08500,
        "stop_loss": 1.08200,
        "take_profit": 1.09000,
        "reasoning": "SMA bullish crossover with supportive ECB commentary",
        "chart_analysis": "Uptrend visible with bullish engulfing pattern",
        "risk_factors": ["NFP release tomorrow", "Thin liquidity"],
    }

    trade_id = record_trade(demo_analysis)
    trade = close_trade(trade_id, 1.08350)  # Simulated loss
    if trade:
        pm = perform_post_mortem(trade_id)
        print(json.dumps(pm, indent=2))

    stats = get_performance_stats()
    print(f"\nPerformance: {json.dumps(stats, indent=2)}")
    print(f"\nLessons: {get_recent_lessons()}")
