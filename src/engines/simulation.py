import numpy as np
import time

class MonteCarloEngine:
    """
    Cỗ máy giả lập tương lai Titan Aegis.
    Sử dụng thuật toán Geometric Brownian Motion (GBM) để dự báo giá.
    """
    def __init__(self, num_simulations=1000, time_horizon=60):
        self.num_sim = num_simulations  # Số lượng vũ trụ song song (1000)
        self.minutes = time_horizon     # Thời gian dự báo (60 phút)

    def run(self, current_price, volatility_min, trend_bias, tp_price, sl_price):
        """
        Chạy mô phỏng.
        - volatility_min: ATR chia cho giá (Biến động % mỗi phút)
        - trend_bias: Xu hướng dòng tiền (vd: 0.0001 là tăng nhẹ)
        """
        start_time = time.time()
        
        # 1. TẠO MA TRẬN BIẾN ĐỘNG (Vectorized - Siêu tốc)
        # Tạo 1000 kịch bản cùng lúc, không dùng vòng lặp for chậm chạp
        daily_returns = np.random.normal(
            loc=trend_bias,       
            scale=volatility_min, 
            size=(self.minutes, self.num_sim)
        )
        
        # 2. TÍNH ĐƯỜNG GIÁ (Cộng dồn biến động)
        price_paths = current_price * (1 + daily_returns).cumprod(axis=0)
        
        # 3. PHÂN TÍCH KẾT QUẢ (THE VERDICT)
        # Kiểm tra xem mỗi kịch bản chạm TP hay SL trước?
        
        # Tạo mảng kết quả: 0=Chưa rõ, 1=Thắng, -1=Thua
        results = np.zeros(self.num_sim)
        
        # Tìm điểm chạm TP (Target)
        # np.argmax trả về chỉ số đầu tiên thỏa mãn điều kiện
        hit_tp_mask = np.any(price_paths >= tp_price, axis=0)
        tp_indices = np.argmax(price_paths >= tp_price, axis=0)
        # Nếu không chạm, gán index = vô cực để so sánh
        tp_indices[~hit_tp_mask] = 99999 

        # Tìm điểm chạm SL (Stoploss)
        hit_sl_mask = np.any(price_paths <= sl_price, axis=0)
        sl_indices = np.argmax(price_paths <= sl_price, axis=0)
        sl_indices[~hit_sl_mask] = 99999

        # So sánh: Cái nào xảy ra trước?
        wins = np.sum(tp_indices < sl_indices)
        ruins = np.sum(sl_indices < tp_indices)
        # Những trường hợp còn lại là Hết giờ (Time Exit) -> Coi như hòa hoặc xử lý sau
        
        exec_time = time.time() - start_time
        
        # Tính xác suất
        win_rate = (wins / self.num_sim) * 100
        ruin_rate = (ruins / self.num_sim) * 100
        
        # Đánh giá rủi ro (Risk Score 1-10)
        # Nếu tỷ lệ cháy > 30% -> Rủi ro cực cao (Score thấp)
        risk_score = 10
        if ruin_rate > 10: risk_score -= 2
        if ruin_rate > 30: risk_score -= 3
        if ruin_rate > 50: risk_score -= 5
        if win_rate < 50: risk_score = 0
        
        return {
            "win_probability": round(win_rate, 2),
            "ruin_probability": round(ruin_rate, 2),
            "risk_score": risk_score,
            "execution_time": f"{exec_time:.4f}s",
            "metadata": {
                "simulations": self.num_sim,
                "horizon_mins": self.minutes
            }
        }