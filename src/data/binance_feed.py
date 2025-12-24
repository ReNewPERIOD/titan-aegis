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

    def get_market_snapshot(self):
        """
        Lấy dữ liệu thị trường tươi sống: Giá, Volatility (ATR), Trend
        """
        try:
            # 1. Lấy nến lịch sử (OHLCV) - Lấy 50 nến gần nhất
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=50)
            
            if not ohlcv:
                return None

            # 2. Chuyển sang DataFrame để tính toán
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 3. Tính Volatility (ATR - Average True Range)
            # Công thức đơn giản hóa: Trung bình (High - Low) của 14 nến
            df['tr'] = df['high'] - df['low']
            atr = df['tr'].rolling(window=14).mean().iloc[-1]
            
            # 4. Tính Trend Bias (Dòng tiền)
            # Đơn giản: Giá đóng cửa so với MA20 (Bollinger Middle)
            ma20 = df['close'].rolling(window=20).mean().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Bias dương nếu giá > MA20, âm nếu < MA20
            # Chuẩn hóa về dạng % (ví dụ 0.001 là 0.1%)
            bias = (current_price - ma20) / ma20 

            return {
                "symbol": self.symbol,
                "price": current_price,
                "volatility": atr / current_price, # ATR dạng %
                "atr_value": atr,
                "bias": bias,
                "trend": "UP" if bias > 0 else "DOWN"
            }

        except Exception as e:
            print(Fore.RED + f"❌ Lỗi Data Feed: {e}")
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