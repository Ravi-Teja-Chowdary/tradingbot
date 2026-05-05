# EUR/USD VisionPulse AI - How To Use

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Get API Keys (Free)](#2-get-api-keys-free)
3. [Installation](#3-installation)
4. [Configuration](#4-configuration)
5. [Running the App](#5-running-the-app)
6. [Dashboard Usage](#6-dashboard-usage)
7. [Architecture Overview](#7-architecture-overview)
8. [File Structure](#8-file-structure)
9. [Troubleshooting](#9-troubleshooting)
10. [Running on Replit](#10-running-on-replit)

---

## 1. Prerequisites

Before running the app, ensure the following are installed on your laptop:

### Python 3.10 or higher
- **Windows:** Download from [python.org](https://www.python.org/downloads/). During installation, **check "Add Python to PATH"**.
- **Mac:** `brew install python` or download from python.org.
- **Linux:** `sudo apt install python3 python3-pip python3-venv`

Verify installation:
```bash
python --version    # Should show 3.10+
pip --version       # Should show pip for Python 3.10+
```

### Git (optional, for cloning)
- Download from [git-scm.com](https://git-scm.com/)

---

## 2. Get API Keys (Free)

You need **two** API keys. Both have free tiers:

### A) Google Gemini API Key (Required)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (starts with `AIza...`)
5. The **free tier** allows 15 requests/minute, which is more than enough

### B) NewsAPI Key (Required)
1. Go to [NewsAPI.org](https://newsapi.org/register)
2. Create a free account
3. After registration, your API key will be shown on the dashboard
4. Copy the key
5. The **free tier** allows 100 requests/day (more than enough for 30-min intervals)

### C) EODHD API Key (Optional backup)
1. Go to [EODHD.com](https://eodhd.com/register)
2. Sign up for the free tier
3. Your API key will be on the dashboard
4. This is an optional fallback if NewsAPI is down

---

## 3. Installation

### Step 1: Open a Terminal
- **Windows:** Open PowerShell or Command Prompt
- **Mac/Linux:** Open Terminal

### Step 2: Navigate to the project folder
```bash
cd "C:\Users\Ravi Teja\Documents\Tradingbot"
```
(Or wherever you saved the project files)

### Step 3: Create a virtual environment (recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it:
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt):
.\venv\Scripts\activate.bat

# Mac/Linux:
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### Step 4: Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Install Playwright browsers
```bash
python -m playwright install chromium
```

This downloads the Chromium browser (~150MB) that Playwright uses for chart screenshots.

> **Note:** If `playwright install` asks for system dependencies on Linux, run:
> ```bash
> python -m playwright install-deps
> ```

---

## 4. Configuration

### Step 1: Create your `.env` file
Copy the example file and add your real API keys:

```bash
# Windows (PowerShell):
Copy-Item .env.example .env

# Mac/Linux:
cp .env.example .env
```

### Step 2: Edit the `.env` file
Open `.env` in any text editor (Notepad, VS Code, nano, etc.) and replace the placeholder values:

```env
# Google Gemini API Key
GEMINI_API_KEY=AIzaSyD_YOUR_REAL_KEY_HERE

# NewsAPI Key
NEWSAPI_KEY=your_real_newsapi_key_here

# Optional: EODHD API Key
# EODHD_API_KEY=your_eodhd_key_here
```

> **IMPORTANT:** Never commit your `.env` file to Git. It contains sensitive API keys.

---

## 5. Running the App

There are several ways to run VisionPulse AI:

### Option A: Full System (Recommended)
Starts both the analysis engine (30-min loops) AND the dashboard:
```bash
python run.py
```
This will:
- Launch the Streamlit dashboard at **http://localhost:8501**
- Start the analysis engine running every 30 minutes
- The first analysis runs immediately

### Option B: Single Analysis Run + Dashboard
Run one analysis cycle, then just view results in the dashboard:
```bash
python run.py --once
```

### Option C: Dashboard Only
If you've already run an analysis and just want to view results:
```bash
python run.py --dashboard-only
```
Or run Streamlit directly:
```bash
streamlit run dashboard.py
```

### Option D: Engine Only (No Dashboard)
Run the analysis loop without the web UI:
```bash
python main.py              # Continuous loop (30-min default)
python main.py --once       # Single run
python main.py 15           # Custom interval: every 15 minutes
```

### Option E: Custom interval
```bash
python run.py 15     # Run analysis every 15 minutes instead of 30
```

### Stopping the App
Press **Ctrl+C** in the terminal to gracefully stop all processes.

---

## 6. Dashboard Usage

After starting the app, open your browser and go to:
```
http://localhost:8501
```

### Dashboard Sections:

| Section | Description |
|---------|-------------|
| **Top Metrics** | Shows current trade thesis (Bullish/Bearish/Neutral), confidence score, win rate, and total trades |
| **Chart** | The latest TradingView EUR/USD screenshot captured by the bot |
| **AI Analysis** | Expandable sections for chart, technical, and fundamental analysis |
| **Trade Levels** | Suggested entry, stop-loss, and take-profit prices |
| **Risk Factors** | Identified risks for the current market conditions |
| **Quantitative Data** | Raw OHLCV data and technical indicators |
| **News Intelligence** | Latest headlines and sentiment analysis |
| **Performance Stats** | Running statistics on prediction accuracy |
| **Lessons Learned** | The AI's self-generated notes from past mistakes |
| **Trade History** | Table of all simulated trades with outcomes |
| **Cycle Log** | Timestamps and details of each analysis run |

### Sidebar Controls:
- **Auto-refresh:** Toggle automatic dashboard refresh (default: every 30 seconds)
- **Refresh Now:** Manually refresh the dashboard

---

## 7. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    EUR/USD VisionPulse AI                     │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Visual   │ Quant    │ News     │ Gemini   │ Self-Learning   │
│ Percep.  │ Data     │ Intel    │ Brain    │ Loop            │
│          │          │          │          │                 │
│Playwright│ yfinance │ NewsAPI  │Gemini 1.5│ memory.json     │
│→ Screenshot→ OHLCV  │→ Headlines│ Flash   │→ Post-Mortems   │
│          │→ SMA/RSI │→ Sentiment│         │→ Lessons        │
│          │→ ATR     │          │          │→ Strategy Adj.  │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                      Main Orchestrator                       │
│            (30-min loop, coordinates all modules)            │
├─────────────────────────────────────────────────────────────┤
│                    Streamlit Dashboard                        │
│           (http://localhost:8501, auto-refresh)               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow:
1. **Every 30 minutes**, the orchestrator triggers a new cycle
2. **Playwright** captures a TradingView chart screenshot
3. **yfinance** fetches the latest OHLCV data and technical indicators
4. **NewsAPI** pulls recent financial headlines about ECB, Fed, EUR/USD, etc.
5. **Gemini 1.5 Flash** receives the screenshot + data + news and produces a trade thesis
6. If the thesis is Bullish or Bearish (confidence ≥ 40%), a **simulated trade** is opened
7. Old trades are **auto-closed** after 1 hour using the current price
8. A **post-mortem** is run on each closed trade, comparing prediction to actual outcome
9. Any **lessons** from mistakes are fed back into the next analysis cycle
10. Results are saved to JSON files and displayed on the **Streamlit dashboard**

---

## 8. File Structure

```
Tradingbot/
├── .env                    # Your API keys (you create this)
├── .env.example            # Template for API keys
├── requirements.txt        # Python package dependencies
│
├── run.py                  # Launcher: starts engine + dashboard
├── main.py                 # Orchestrator: runs the 30-min analysis loop
├── config.py               # Central configuration
│
├── visual_perception.py    # Playwright screenshot capture
├── quantitative_data.py    # yfinance OHLCV + technical indicators
├── fundamental_intel.py    # NewsAPI headline fetching + sentiment
├── multimodal_brain.py     # Gemini 1.5 Flash AI analysis
├── learning_loop.py        # Self-learning memory system
│
├── dashboard.py            # Streamlit web UI
│
├── memory.json             # Trade history + lessons database
├── latest_analysis.json    # Most recent analysis (auto-generated)
├── cycle_log.json          # Run history (auto-generated)
│
├── screenshots/            # Chart screenshots (auto-created)
│   └── eurusd_YYYYMMDD_HHMMSS.png
│
└── How_To_Use.md           # This file
```

---

## 9. Troubleshooting

### "GEMINI_API_KEY environment variable is not set"
- Make sure you created the `.env` file (not `.env.example`)
- Make sure the key is correct with no extra spaces
- Restart the app after changing `.env`

### "NewsAPI error: 401"
- Your NewsAPI key is invalid or expired
- Go to [newsapi.org/account](https://newsapi.org/account) and get a new key
- The free tier only works for `everything` endpoint (not `top-headlines` from production)

### Playwright browser not found
```bash
python -m playwright install chromium
```
On Linux, you may also need:
```bash
python -m playwright install-deps
```

### Screenshot capture fails
- This is normal behind corporate firewalls or on some cloud hosts
- The app creates a placeholder image and continues with text-only AI analysis
- The AI will use quantitative data + news even without the chart image

### "No data returned from yfinance"
- EUR/USD data may be delayed outside forex market hours (Mon-Fri)
- yfinance requires internet access
- Try: `python -c "import yfinance; print(yfinance.Ticker('EURUSD=X').history(period='1d'))"`

### Streamlit won't start
```bash
pip install streamlit --upgrade
streamlit run dashboard.py --server.port=8501
```
If port 8501 is in use, try a different port:
```bash
streamlit run dashboard.py --server.port=8502
```

### Memory.json corrupted
Delete it and it will be re-created:
```bash
# Windows:
del memory.json

# Mac/Linux:
rm memory.json
```

### PowerShell script execution policy (Windows)
If you can't activate the virtual environment in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 10. Running on Replit

To deploy this on Replit:

1. **Create a new Python Repl** on [replit.com](https://replit.com)

2. **Upload all files** from this project to the Repl

3. **Set environment variables** in Replit:
   - Click the 🔒 **Secrets** tab in the left sidebar
   - Add these secrets:
     - `GEMINI_API_KEY` = your key
     - `NEWSAPI_KEY` = your key

4. **Configure the run command** in `.replit` file:
   ```
   run = "pip install -r requirements.txt && python -m playwright install chromium && python run.py --once"
   ```

5. Or for continuous mode, create a `.replit` file:
   ```toml
   run = "python run.py"
   
   [nix]
   channel = "stable-23_11"
   
   [deployment]
   run = ["sh", "-c", "python run.py"]
   ```

6. **Install system dependencies** (in Replit Shell):
   ```bash
   pip install -r requirements.txt
   python -m playwright install chromium
   python -m playwright install-deps
   ```

7. Click **Run** — the dashboard will be available on your Replit's public URL

> **Note:** Replit's free tier may have resource limits. The app is designed to work within free-tier constraints for all APIs.

---

## Quick Start (TL;DR)

```bash
# 1. Navigate to project
cd "path/to/Tradingbot"

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1    # Windows PowerShell

# 3. Install everything
pip install -r requirements.txt
python -m playwright install chromium

# 4. Set up API keys
copy .env.example .env
# Edit .env with your real API keys

# 5. Run!
python run.py
# Open http://localhost:8501 in your browser
```

---

**Disclaimer:** This is a simulated trading tool for educational purposes only. It does not execute real trades and is not financial advice. Always do your own research before making investment decisions.
