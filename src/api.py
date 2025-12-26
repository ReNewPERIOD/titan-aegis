from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data.binance_feed import BinanceFeed
from engines.simulation import MonteCarloEngine
from execution.paper_trader import PaperTrader

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

feed = BinanceFeed(symbol='BTC/USDT')

@app.get("/")
def read_root():
    return {"status": "Titan Aegis System Online"}

@app.get("/market-data")
def market_data(tf: str = "15m"): 
    return feed.get_market_snapshot(timeframe=tf)

# 👇👇👇 API MỚI 👇👇👇
@app.get("/technical-indicators")
def get_technical_indicators(tf: str = "15m"):
    return feed.get_technical_indicators(timeframe=tf)
# 👆👆👆

@app.get("/simulation-paths")
def get_simulation_paths(tf: str = "15m"):
    # ... (Giữ nguyên code Simulation đã fix ở bài trước) ...
    data = feed.get_market_snapshot(timeframe=tf)
    if not data: return {"error": "No Data"}
    current_price = data['price']
    volatility_pct = (data['atr'] / current_price) * 2 
    trend_factor = 0.002 if data['trend'] == 'UP' else -0.002
    steps = 60
    paths = 50 
    random_shocks = np.random.normal(trend_factor, volatility_pct, (steps, paths))
    price_paths = current_price * (1 + random_shocks).cumprod(axis=0)
    return {
        "paths": price_paths.tolist(), 
        "mean_path": np.mean(price_paths, axis=1).tolist()
    }

@app.get("/volatility-analysis")
def volatility_analysis(tf: str = "1h"):
    return feed.get_historical_volatility(days=30)
        
@app.get("/trade-logs")
def get_trade_logs():
    return [
        {"Timestamp": "14:58:27", "Action": "SHORT", "Price": 86980, "Score": 15},
        {"Timestamp": "14:57:21", "Action": "SHORT", "Price": 87015, "Score": 15},
        {"Timestamp": "14:56:16", "Action": "SHORT", "Price": 87043, "Score": 14},
    ]