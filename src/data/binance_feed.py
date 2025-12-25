import ccxt
import pandas as pd
import numpy as np
import time
from colorama import Fore

class BinanceFeed:
    def __init__(self, symbol='BTC/USDT', timeframe='15m'):
        self.symbol = symbol
        self.timeframe = timeframe
        # Khởi tạo sàn Binance (chế độ không cần API Key để lấy giá - Public Data)
        self.exchange = ccxt.binance({'enableRateLimit': True})
    
    def get_historical_volatility(self, days=30):
        """
        [NÂNG CẤP] Trả về cả biểu đồ hourly VÀ các chỉ số thống kê (Stats)
        """
        try:
            limit = 24 * days
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1h', limit=limit)
            if not ohlcv: return {}

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['hour'] = df['timestamp'].dt.hour + 7 # Giờ Việt Nam
            df['hour'] = df['hour'].apply(lambda x: x - 24 if x >= 24 else x)
            
            # Tính biến động % (High - Low)
            df['volatility'] = (df['high'] - df['low']) / df['open'] * 100 
            
            # 1. TÍNH CÁC CHỈ SỐ THỐNG KÊ (STATS)
            avg_vol = df['volatility'].mean()            # Biến động TB mỗi giờ
            peak_vol = df['volatility'].max()            # Cây nến biến động mạnh nhất lịch sử
            
            # Tìm giờ biến động mạnh nhất (Peak Time)
            hourly_group = df.groupby('hour')['volatility'].mean()
            best_hour = hourly_group.idxmax()            # Giờ nào biến động mạnh nhất
            best_hour_vol = hourly_group.max()           # Giá trị biến động của giờ đó
            
            # 2. DỮ LIỆU BIỂU ĐỒ (CHART)
            hourly_stats = hourly_group.reset_index()
            hourly_stats['volatility'] = hourly_stats['volatility'].round(2)
            
            return {
                "chart": hourly_stats.to_dict(orient='records'),
                "stats": {
                    "avg_intraday": round(avg_vol, 2),
                    "peak_intraday": round(peak_vol, 2),
                    "best_hour": f"{best_hour}:00",
                    "best_hour_vol": round(best_hour_vol, 2)
                }
            }
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return {}

    # Tìm hàm này và sửa dòng đầu tiên (thêm tham số timeframe)
    def get_market_snapshot(self, timeframe='1h'): # <--- THÊM timeframe
        try:
            # Lấy nến theo đúng timeframe người dùng chọn
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=100)
            if not ohlcv: return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # --- TÍNH TOÁN CÁC CHỈ SỐ THEO TIMEFRAME ĐÓ ---
            current_price = df['close'].iloc[-1]
            
            # 1. Tính ATR (Biến động)
            df['tr0'] = abs(df['high'] - df['low'])
            df['tr1'] = abs(df['high'] - df['close'].shift())
            df['tr2'] = abs(df['low'] - df['close'].shift())
            df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
            atr = df['tr'].rolling(14).mean().iloc[-1]

            # 2. Tính Volume Power (Cho khung nhỏ như 3m, 5m)
            # Nếu Volume hiện tại > Trung bình 20 cây nến trước => Cá mập vào hàng
            vol_ma = df['volume'].rolling(20).mean().iloc[-1]
            current_vol = df['volume'].iloc[-1]
            vol_power = (current_vol / vol_ma) * 100 # >100% là volume mạnh

            # 3. Tính Xu hướng (Trend)
            sma_fast = df['close'].rolling(7).mean().iloc[-1] # Nhanh hơn cho scalping
            sma_slow = df['close'].rolling(25).mean().iloc[-1]
            trend = "UP" if sma_fast > sma_slow else "DOWN"

            # 4. Tính Winrate (AI Confidence) - Càng nhiều Volume càng uy tín
            base_winrate = 50
            if trend == "UP": base_winrate += 10
            if vol_power > 120: base_winrate += 15 # Volume đột biến cộng thêm điểm
            
            return {
                "symbol": self.symbol,
                "price": current_price,
                "atr": atr,
                "trend": trend,
                "winrate": min(base_winrate, 99), # Max 99%
                "volume_power": round(vol_power, 2) # Trả về thêm chỉ số Volume
            }
        except Exception as e:
            print(f"Error: {e}")
            return None

# --- TEST MODULE ---
if __name__ == "__main__":
    feed = BinanceFeed()
    print(Fore.CYAN + "📡 Đang kết nối vệ tinh tới Binance...")
    
    data = feed.get_market_snapshot()
    
    if data:
        print(Fore.GREEN + f"\n✅ DỮ LIỆU THỰC TẾ ({data['symbol']}):")
        print(f"   💰 Giá hiện tại: ${data['price']:,.2f}")
        print(f"   🌊 Biến động (ATR): {data['atr_value']:.2f} giá/nến ({data['volatility']*100:.4f}%)")
        print(f"   tj Xu hướng (Bias): {data['bias']:.6f} ({data['trend']})")
    else:
        print(Fore.RED + "Không lấy được dữ liệu.")