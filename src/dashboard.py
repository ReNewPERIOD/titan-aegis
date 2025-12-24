import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import sys
import os
import numpy as np

# Import core modules
sys.path.append(os.path.abspath("src"))
from data.binance_feed import BinanceFeed
from engines.simulation import MonteCarloEngine

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Titan Aegis V7 Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Tùy chỉnh (Giao diện Dark Mode Pro)
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #00ffcc; font-weight: bold;}
    div[data-testid="stMetricLabel"] { font-size: 14px; color: #888; }
    .css-1d391kg { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🛡️ TITAN AEGIS V7")
    st.caption("AI-Powered Hedge Fund Dashboard")
with c2:
    if st.button('🔄 REFRESH SYSTEM', use_container_width=True):
        st.rerun()

# --- LẤY DỮ LIỆU ---
feed = BinanceFeed(symbol='BTC/USDT')
data = feed.get_market_snapshot()

if not data:
    st.error("📡 MẤT KẾT NỐI VỆ TINH BINANCE!")
    st.stop()

# --- KHỐI 1: TỔNG QUAN THỊ TRƯỜNG ---
st.markdown("### 📊 MARKET OVERVIEW")
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("💰 BTC PRICE", f"${data['price']:,.2f}", delta=None)
with k2:
    st.metric("🌊 VOLATILITY (ATR)", f"{data['atr_value']:.2f}", help="Biến động giá trung bình 15p")
with k3:
    trend_color = "normal" if data['trend'] == "UP" else "inverse"
    st.metric("📈 TREND", f"{data['trend']}", delta=f"{data['bias']*100:.4f}%", delta_color=trend_color)

# Chạy nhanh Monte Carlo cho hiển thị
engine = MonteCarloEngine(num_simulations=500)
# Giả định Setup theo Trend
if data['trend'] == "UP":
    tp = data['price'] + (data['atr_value'] * 2)
    sl = data['price'] - (data['atr_value'] * 1.5)
else:
    tp = data['price'] - (data['atr_value'] * 2)
    sl = data['price'] + (data['atr_value'] * 1.5)

res = engine.run(data['price'], data['volatility'], data['bias'], tp, sl)
winrate = res['win_probability']

with k4:
    st.metric("🎲 AI WINRATE", f"{winrate}%", delta="Monte Carlo Forecast")

# --- KHỐI 2: TRỰC QUAN HÓA (VISUALIZATION) ---
col_chart, col_gauge = st.columns([2, 1])

with col_chart:
    st.markdown("#### 🔮 TƯƠNG LAI GIẢ LẬP (1 GIỜ TỚI)")
    
    # Tạo dữ liệu vẽ biểu đồ
    steps = 60
    paths = 100
    # Tạo ngẫu nhiên 100 con đường
    random_walks = np.random.normal(data['bias'], data['volatility'], (steps, paths))
    price_paths = data['price'] * (1 + random_walks).cumprod(axis=0)
    
    # Tính đường trung bình (Mean Path) - Đường màu vàng
    mean_path = np.mean(price_paths, axis=1)

    fig = go.Figure()

    # 1. Vẽ 100 sợi dây mờ (Làm nền)
    for i in range(paths):
        fig.add_trace(go.Scatter(y=price_paths[:, i], mode='lines', 
                                 line=dict(color='rgba(0, 255, 204, 0.05)', width=1), 
                                 hoverinfo='skip', showlegend=False))
        
    # 2. Vẽ đường Trung bình (Đậm, Rõ) - Hướng đi chính của thị trường
    fig.add_trace(go.Scatter(y=mean_path, mode='lines', name='Dự báo trung bình',
                             line=dict(color='#ffcc00', width=3)))

    # 3. Vẽ TP / SL
    fig.add_hline(y=tp, line_dash="dash", line_color="#00ff00", annotation_text="TP (Chốt lời)", annotation_font_color="#00ff00")
    fig.add_hline(y=sl, line_dash="dash", line_color="#ff0000", annotation_text="SL (Cắt lỗ)", annotation_font_color="#ff0000")

    # Trang trí biểu đồ
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=350,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(showgrid=False, title="Phút (Tương lai)"),
        yaxis=dict(showgrid=True, gridcolor='#333')
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"💡 **Giải thích:** Đường màu vàng là hướng đi khả thi nhất. Nếu nó chạm vạch Xanh lá (TP) -> Kèo thơm.")

with col_gauge:
    st.markdown("#### 🏛️ ĐIỂM SỐ TITAN")
    
    # Logic chấm điểm sơ bộ để hiển thị
    score = 0
    if winrate > 60: score += 10
    if winrate > 80: score += 2
    # Đây chỉ là điểm giả lập hiển thị, điểm thật nằm trong log
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Confidence Score (0-15)"},
        gauge = {
            'axis': {'range': [None, 15], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#00ffcc"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 7], 'color': '#ff3333'},
                {'range': [7, 13], 'color': '#ffcc00'},
                {'range': [13, 15], 'color': '#00ff00'}],
        }))
    
    fig_gauge.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family="Arial"),
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

# --- KHỐI 3: LOGS ---
st.markdown("### 📜 NHẬT KÝ LỆNH (PAPER TRADING)")
log_file = "logs/titan_paper_trades.csv"

if os.path.exists(log_file):
    df = pd.read_csv(log_file)
    df = df.sort_values(by="Timestamp", ascending=False)
    
    # Hiển thị bảng đẹp hơn
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Timestamp": "Thời gian",
            "Symbol": "Cặp tiền",
            "Action": "Lệnh",
            "Price": st.column_config.NumberColumn("Giá vào", format="$%.2f"),
            "TP": st.column_config.NumberColumn("TP", format="$%.2f"),
            "SL": st.column_config.NumberColumn("SL", format="$%.2f"),
            "Score": st.column_config.NumberColumn("Điểm", format="%d ⭐"),
        }
    )
else:
    st.info("Chưa có dữ liệu lệnh.")