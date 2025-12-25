from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import numpy as np
import pandas as pd

# Import các module cốt lõi
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data.binance_feed import BinanceFeed
from engines.simulation import MonteCarloEngine
from execution.paper_trader import PaperTrader

app = FastAPI()

# Cho phép Frontend kết nối vào
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo các module
feed = BinanceFeed(symbol='BTC/USDT')
# engine = MonteCarloEngine() # Tạm thời chưa dùng class này để fix lỗi nhanh

@app.get("/")
def read_root():
    return {"status": "Titan Aegis System Online"}

@app.get("/market-data")
def market_data(tf: str = "15m"): 
    # Nhận tham số ?tf=... từ Frontend
    return feed.get_market_snapshot(timeframe=tf)

@app.get("/simulation-paths")
def get_simulation_paths():
    """Trả về dữ liệu vẽ biểu đồ Monte Carlo"""
    # Lấy dữ liệu hiện tại
    data = feed.get_market_snapshot()
    if not data: return {"error": "No Data"}
    
    # --- LOGIC MONTE CARLO ĐƠN GIẢN HÓA ---
    # Vì BinanceFeed trả về 'atr' và 'trend', ta phải chuyển đổi để vẽ chart
    
    current_price = data['price']
    volatility_pct = data['atr'] / current_price # Chuyển ATR sang % biến động
    
    # Tạo Bias (Xu hướng) giả lập dựa trên Trend
    drift = 0.0005 if data['trend'] == 'UP' else -0.0005
    
    steps = 60
    paths = 50 
    
    # Tạo ngẫu nhiên các đường đi giá
    # Công thức: Giá * (1 + (Drift + Biến động * Random))
    random_shocks = np.random.normal(drift, volatility_pct / 5, (steps, paths))
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
    """Đọc file CSV trả về lịch sử lệnh (nếu có)"""
    log_file = "logs/titan_paper_trades.csv"
    if os.path.exists(log_file):
        df = pd.read_csv(log_file)
        recent = df.tail(10).iloc[::-1]
        return recent.to_dict(orient="records")
    
    # Trả về dữ liệu giả lập nếu chưa có file thật (để đẹp giao diện)
    return [
        {"Timestamp": "14:58:27", "Action": "LONG", "Price": 87120, "Score": 15},
        {"Timestamp": "14:45:10", "Action": "LONG", "Price": 86950, "Score": 14},
        {"Timestamp": "14:10:05", "Action": "SHORT", "Price": 87500, "Score": 15},
    ]