import ccxt
import pandas as pd
import numpy as np
import time
from colorama import Fore

class BinanceFeed:
    def __init__(self, symbol='BTC/USDT'):
        self.symbol = symbol
        # Khởi tạo sàn Binance (chế độ không cần API Key để lấy giá - Public Data)
        self.exchange = ccxt.binance({'enableRateLimit': True})
    
    def get_market_snapshot(self, timeframe='15m'): 
        """
        Lấy dữ liệu thị trường real-time theo khung giờ (3m, 15m, 1h...)
        """
        try:
            # 1. Lấy nến
            limit = 50 
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            if not ohlcv: return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # --- TÍNH TOÁN CHỈ SỐ ---
            current_price = df['close'].iloc[-1]
            
            # A. ATR (Biến động giá tuyệt đối)
            df['tr0'] = abs(df['high'] - df['low'])
            df['tr1'] = abs(df['high'] - df['close'].shift())
            df['tr2'] = abs(df['low'] - df['close'].shift())
            df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
            atr = df['tr'].rolling(14).mean().iloc[-1]

            # B. XU HƯỚNG (TREND)
            # Khung nhỏ (3m, 5m) dùng MA ngắn để nhạy sóng
            fast_p = 7 if timeframe in ['3m', '5m'] else 14
            slow_p = 25 if timeframe in ['3m', '5m'] else 50
            
            ma_fast = df['close'].rolling(fast_p).mean().iloc[-1]
            ma_slow = df['close'].rolling(slow_p).mean().iloc[-1]
            trend = "UP" if ma_fast > ma_slow else "DOWN"

            # C. VOLUME POWER
            vol_ma = df['volume'].rolling(20).mean().iloc[-1]
            current_vol = df['volume'].iloc[-1]
            # >100% là tiền vào mạnh
            vol_power = (current_vol / vol_ma) * 100 if vol_ma > 0 else 0

            # D. WINRATE (AI SCORE)
            base_winrate = 50
            last_close = df['close'].iloc[-1]
            last_open = df['open'].iloc[-1]
            is_green = last_close > last_open
            
            # Cộng điểm nếu Trend khớp màu nến
            if (trend == "UP" and is_green) or (trend == "DOWN" and not is_green):
                base_winrate += 15
            
            # Cộng điểm nếu Volume đột biến
            if vol_power > 120: base_winrate += 10
            
            return {
                "symbol": self.symbol,
                "price": current_price,
                "atr": atr, # Giá trị tuyệt đối (VD: 150$)
                "trend": trend,
                "winrate": min(base_winrate, 99),
                "volume_power": round(vol_power, 1)
            }

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None

    def get_historical_volatility(self, days=30):
        try:
            limit = 24 * days
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1h', limit=limit)
            if not ohlcv: return {}

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['hour'] = df['timestamp'].dt.hour + 7 # Giờ Việt Nam
            df['hour'] = df['hour'].apply(lambda x: x - 24 if x >= 24 else x)
            
            # Tính biến động %
            df['volatility'] = (df['high'] - df['low']) / df['open'] * 100 
            
            hourly_group = df.groupby('hour')['volatility'].mean()
            best_hour = hourly_group.idxmax()
            best_hour_vol = hourly_group.max()
            
            hourly_stats = hourly_group.reset_index()
            hourly_stats['volatility'] = hourly_stats['volatility'].round(2)
            
            return {
                "chart": hourly_stats.to_dict(orient='records'),
                "stats": {
                    "avg_intraday": round(df['volatility'].mean(), 2),
                    "peak_intraday": round(df['volatility'].max(), 2),
                    "best_hour": f"{best_hour}:00",
                    "best_hour_vol": round(best_hour_vol, 2)
                }
            }
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return {}

# --- TEST MODULE ---
if __name__ == "__main__":
    feed = BinanceFeed()
    print(Fore.CYAN + "📡 Đang kết nối vệ tinh tới Binance...")
    data = feed.get_market_snapshot()
    if data:
        print(Fore.GREEN + f"\n✅ DỮ LIỆU THỰC TẾ ({data['symbol']}):")
        print(f"   💰 Giá: ${data['price']:,.2f}")
        print(f"   🌊 ATR: {data['atr']:.2f}")
        print(f"   📈 Trend: {data['trend']}")
    else:
        print(Fore.RED + "Không lấy được dữ liệu.")