import ccxt
import pandas as pd
import numpy as np
import time
from colorama import Fore

class BinanceFeed:
    def __init__(self, symbol='BTC/USDT'):
        self.symbol = symbol
        self.exchange = ccxt.binance({'enableRateLimit': True})
    
    # ... (Giữ nguyên hàm get_market_snapshot cũ của bạn ở đây) ...
    def get_market_snapshot(self, timeframe='15m'):
        # ... (Code cũ giữ nguyên không thay đổi) ...
        try:
            print(f"📡 API Called: Fetching Binance Data for Timeframe: [{timeframe}]")
            limit = 50 
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            if not ohlcv: return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            current_price = df['close'].iloc[-1]
            
            df['tr0'] = abs(df['high'] - df['low'])
            df['tr1'] = abs(df['high'] - df['close'].shift())
            df['tr2'] = abs(df['low'] - df['close'].shift())
            df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
            atr = df['tr'].rolling(14).mean().iloc[-1]

            fast_p = 7 if timeframe in ['3m', '5m'] else 14
            slow_p = 25 if timeframe in ['3m', '5m'] else 50
            
            ma_fast = df['close'].rolling(fast_p).mean().iloc[-1]
            ma_slow = df['close'].rolling(slow_p).mean().iloc[-1]
            trend = "UP" if ma_fast > ma_slow else "DOWN"

            vol_ma = df['volume'].rolling(20).mean().iloc[-1]
            current_vol = df['volume'].iloc[-1]
            vol_power = (current_vol / vol_ma) * 100 if vol_ma > 0 else 0

            base_winrate = 50
            last_close = df['close'].iloc[-1]
            last_open = df['open'].iloc[-1]
            is_green = last_close > last_open
            
            if (trend == "UP" and is_green) or (trend == "DOWN" and not is_green):
                base_winrate += 15
            
            if vol_power > 120: base_winrate += 10
            
            return {
                "symbol": self.symbol,
                "price": current_price,
                "atr": atr,
                "trend": trend,
                "winrate": min(base_winrate, 99),
                "volume_power": round(vol_power, 1)
            }

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None

    # 👇👇👇 HÀM MỚI: TÍNH TOÁN RSI & MACD 👇👇👇
    def get_technical_indicators(self, timeframe='15m'):
        try:
            # Lấy 100 nến để tính chỉ báo cho mượt
            limit = 100
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            if not ohlcv: return []

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 1. Tính RSI (14)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 2. Tính MACD (12, 26, 9)
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema12 - ema26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']

            # Lấy 30 cây nến cuối cùng để vẽ chart
            df_final = df.tail(30).copy()
            
            # Xử lý dữ liệu lỗi (NaN)
            df_final = df_final.replace({np.nan: None})
            
            return df_final.to_dict(orient='records')

        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            return []

    def get_historical_volatility(self, days=30):
        # ... (Giữ nguyên code cũ của bạn) ...
        try:
            limit = 24 * days
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1h', limit=limit)
            if not ohlcv: return {}

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['hour'] = df['timestamp'].dt.hour + 7 
            df['hour'] = df['hour'].apply(lambda x: x - 24 if x >= 24 else x)
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
            return {}