"""
EUR/USD VisionPulse AI - Launcher Script
Starts both the analysis engine and the Streamlit dashboard.
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

BASE_DIR = Path(__file__).parent


def run_dashboard():
    """Launch the Streamlit dashboard."""
    print("[Launcher] Starting Streamlit dashboard...")
    dashboard_path = str(BASE_DIR / "dashboard.py")
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", dashboard_path,
         "--server.port=8501", "--server.headless=true"],
        cwd=str(BASE_DIR),
    )


def run_engine(mode: str = "loop", interval: int = 30):
    """Launch the analysis engine."""
    print(f"[Launcher] Starting analysis engine (mode={mode})...")
    main_path = str(BASE_DIR / "main.py")
    args = [sys.executable, main_path]
    if mode == "once":
        args.append("--once")
    else:
        args.append(str(interval))
    return subprocess.Popen(args, cwd=str(BASE_DIR))


def main():
    print("=" * 60)
    print("  EUR/USD VisionPulse AI - Launcher")
    print("=" * 60)
    print()

    mode = "loop"
    interval = 30

    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            mode = "once"
        elif sys.argv[1] == "--dashboard-only":
            mode = "dashboard-only"
        else:
            try:
                interval = int(sys.argv[1])
            except ValueError:
                pass

    processes = []

    try:
        # Start dashboard
        dash_proc = run_dashboard()
        processes.append(dash_proc)
        print("[Launcher] Dashboard starting at http://localhost:8501")
        print()

        if mode != "dashboard-only":
            # Give dashboard a moment to start
            time.sleep(3)

            # Start engine
            engine_proc = run_engine(mode, interval)
            processes.append(engine_proc)

            if mode == "once":
                engine_proc.wait()
                print("[Launcher] Single analysis cycle complete.")
                print("[Launcher] Dashboard still running at http://localhost:8501")
                print("[Launcher] Press Ctrl+C to stop.")
                dash_proc.wait()
            else:
                print(f"[Launcher] Engine running with {interval}-minute intervals.")
                print("[Launcher] Press Ctrl+C to stop all processes.")
                print()
                # Wait for either to finish
                engine_proc.wait()

        else:
            print("[Launcher] Dashboard-only mode. Press Ctrl+C to stop.")
            dash_proc.wait()

    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down all processes...")
    finally:
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        print("[Launcher] All processes stopped.")


if __name__ == "__main__":
    main()
