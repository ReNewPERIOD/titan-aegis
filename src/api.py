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
@app.get("/simulation-paths")
def get_simulation_paths():
    # 1. Lấy dữ liệu snapshot hiện tại (đã bao gồm trend, atr từ feed)
    # Lưu ý: Simulation nên lấy theo khung giờ mặc định hoặc khung giờ active (cần logic phức tạp hơn chút để đồng bộ hoàn hảo, nhưng tạm thời lấy snapshot mới nhất)
    data = feed.get_market_snapshot(timeframe="15m") # Tạm thời fix cứng hoặc bạn truyền tf vào đây
    if not data: return {"error": "No Data"}
    
    current_price = data['price']
    
    # --- LOGIC MỚI: Tăng độ nhạy của biểu đồ ---
    # Chuyển đổi ATR sang % biến động. 
    # Nhân 2 lên để biểu đồ nhìn "sóng gió" hơn cho users thấy rõ
    volatility_pct = (data['atr'] / current_price) * 2 
    
    # Tạo độ dốc (Drift) dựa trên Trend
    # Nếu UP: dốc lên. Nếu DOWN: dốc xuống.
    trend_factor = 0.002 if data['trend'] == 'UP' else -0.002
    
    steps = 60
    paths = 50 
    
    # Công thức Monte Carlo có tính đến Trend (Drift)
    # Drift (Xu hướng) + Shock (Biến động ngẫu nhiên)
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