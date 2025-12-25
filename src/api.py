from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import numpy as np

# Import các module cốt lõi
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data.binance_feed import BinanceFeed
from engines.simulation import MonteCarloEngine
from execution.paper_trader import PaperTrader
import pandas as pd

app = FastAPI()

# Cho phép Frontend (Bolt) kết nối vào
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép tất cả (để dev cho dễ)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo các module
feed = BinanceFeed(symbol='BTC/USDT')
engine = MonteCarloEngine(num_simulations=500) # Chạy nhẹ 500 cho API nhanh

@app.get("/")
def read_root():
    return {"status": "Titan Aegis System Online"}

@app.get("/market-data")
def market_data(tf: str = "1h"): # Mặc định là 1h nếu không gửi gì
    # Map từ user (15 Minute) sang code Binance (15m)
    return feed.get_market_snapshot(timeframe=tf)

@app.get("/simulation-paths")
def get_simulation_paths():
    """Trả về dữ liệu để vẽ biểu đồ Monte Carlo (100 đường)"""
    data = feed.get_market_snapshot()
    if not data: return {"error": "No Data"}
    
    steps = 60
    paths = 100 # Gửi 50 đường thôi cho nhẹ JSON
    

    # Tạo ngẫu nhiên
    random_walks = np.random.normal(data['bias'], data['volatility'], (steps, paths))
    price_paths = data['price'] * (1 + random_walks).cumprod(axis=0)
    
    # Chuyển numpy array thành list để gửi qua mạng được
    return {
        "paths": price_paths.tolist(), # Mảng [60, 50]
        "mean_path": np.mean(price_paths, axis=1).tolist()
    }

# ... (các import cũ giữ nguyên)

@app.get("/volatility-analysis")
def volatility_analysis(tf: str = "1h"):
    # Logic tương tự, bạn cần sửa cả hàm get_historical_volatility trong feed để nhận tf
    # Nhưng tạm thời để 1h cho cái này cũng được vì nó là thống kê dài hạn.
    return feed.get_historical_volatility(days=30)
        
@app.get("/trade-logs")
def get_trade_logs():
    """Đọc file CSV trả về lịch sử lệnh"""
    log_file = "logs/titan_paper_trades.csv"
    if os.path.exists(log_file):
        df = pd.read_csv(log_file)
        # Lấy 10 lệnh mới nhất
        recent = df.tail(10).iloc[::-1]
        return recent.to_dict(orient="records")
    return []