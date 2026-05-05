"""
EUR/USD VisionPulse AI - Configuration
Central configuration file for all modules.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# === API Keys (from environment variables) ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "")

# === Trading Parameters ===
TICKER = "EURUSD=X"
ANALYSIS_INTERVAL_MINUTES = 30
TRADE_AUTO_CLOSE_HOURS = 1
MIN_CONFIDENCE_TO_TRADE = 0.4

# === Technical Analysis ===
SMA_SHORT = 10
SMA_LONG = 20
RSI_PERIOD = 14
ATR_PERIOD = 14

# === News ===
NEWS_KEYWORDS = ["ECB", "Federal Reserve", "EUR/USD", "EURUSD", "Inflation", "Interest Rate", "NFP", "CPI"]
MAX_NEWS_ARTICLES = 20

# === Files & Directories ===
SCREENSHOTS_DIR = "screenshots"
MEMORY_FILE = "memory.json"

# === Dashboard ===
DASHBOARD_PORT = 8501
