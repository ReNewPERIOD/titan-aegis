import sys
import os
import time
import json
from colorama import Fore, Style, init

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from data.binance_feed import BinanceFeed
    from engines.simulation import MonteCarloEngine
    from ai.gemini_client import TitanJudge
    from execution.paper_trader import PaperTrader # <--- MỚI
except ImportError as e:
    print(Fore.RED + f"❌ LỖI: Thiếu module. {e}")
    sys.exit(1)

init(autoreset=True)

# --- CẤU HÌNH ---
DEBUG_MODE = False # <--- BẬT CÁI NÀY ĐỂ ÉP BOT VÀO LỆNH TEST
SYMBOL = 'BTC/USDT'

def print_banner():
    print(Fore.CYAN + Style.BRIGHT + """
    ╔══════════════════════════════════════════════════════╗
    ║         TITAN AEGIS V7 - PAPER TRADING MODE          ║
    ╚══════════════════════════════════════════════════════╝
    """)

def main():
    print_banner()
    
    print(Fore.YELLOW + "🔌 Đang khởi động hệ thống...")
    feed = BinanceFeed(symbol=SYMBOL, timeframe='15m')
    judge = TitanJudge()
    trader = PaperTrader(filename="logs/titan_paper_trades.csv") # Lưu vào thư mục logs
    
    # Tạo thư mục logs nếu chưa có
    os.makedirs("logs", exist_ok=True)
    
    print(Fore.GREEN + "✅ Hệ thống sẵn sàng. Loop 60s...")
    if DEBUG_MODE:
        print(Fore.MAGENTA + "⚠️  CHẾ ĐỘ DEBUG ĐANG BẬT: WINRATE SẼ ĐƯỢC HACK LÊN 99% ĐỂ TEST!")

    while True:
        try:
            print(Fore.BLACK + Style.BRIGHT + "\n" + "-"*50)
            print(Fore.CYAN + f"🕒 Quét: {time.strftime('%H:%M:%S')}")
            
            # 1. LẤY DATA
            market_data = feed.get_market_snapshot()
            if not market_data:
                time.sleep(10)
                continue

            current_price = market_data['price']
            atr = market_data['atr_value']
            trend = market_data['trend']
            
            print(Fore.WHITE + f"   💰 Price: ${current_price:,.2f} | ATR: {atr:.2f} | Trend: {trend}")

            # 2. SETUP
            if trend == "UP":
                direction = "LONG"
                tp = current_price + (atr * 2.0)
                sl = current_price - (atr * 1.5)
            else:
                direction = "SHORT"
                tp = current_price - (atr * 2.0)
                sl = current_price + (atr * 1.5)

            # 3. MONTE CARLO
            print(Fore.CYAN + "   🎲 Running Simulation...")
            engine = MonteCarloEngine(num_simulations=1000)
            math_result = engine.run(current_price, market_data['volatility'], market_data['bias'], tp, sl)
            
            win_rate = math_result['win_probability']
            
            # --- HACK WINRATE ĐỂ TEST (CHỈ DÙNG KHI DEBUG) ---
            if DEBUG_MODE:
                print(Fore.MAGENTA + f"   [DEBUG] Winrate gốc: {win_rate}%. Đang Hack lên 99%...")
                win_rate = 99.9
                math_result['win_probability'] = 99.9

            print(f"      -> Winrate: {Fore.GREEN if win_rate > 60 else Fore.RED}{win_rate}%")

            # 4. GATEKEEPER
            if win_rate < 60:
                print(Fore.RED + "   ⛔ TÍN HIỆU RÁC. Bỏ qua.")
                time.sleep(60)
                continue

            # 5. AI JUDGE
            print(Fore.MAGENTA + "   🧠 Calling Gemini Judge...")
            context = f"Trend {trend}. ATR {atr}. Math Winrate {win_rate}%."
            verdict = judge.evaluate(market_data, math_result, context)
            
            score = verdict.get('score', 0)
            decision = verdict.get('decision', 'ERROR')
            reason = verdict.get('reason', 'Unknown')
            
            print(Fore.WHITE + f"   🏛️ AI VERDICT: {decision} (Score: {score}/15)")
            print(f"      Lý do: {reason}")
            
            # 6. EXECUTION (PAPER TRADING)
            if score >= 8 or DEBUG_MODE: # Debug thì cứ vào lệnh luôn
                print(Fore.GREEN + "   🚀 THỰC THI LỆNH (PAPER)...")
                trader.execute_order(
                    symbol=SYMBOL,
                    action=direction,
                    price=current_price,
                    tp=tp,
                    sl=sl,
                    reason=reason,
                    score=score
                )
            else:
                print(Fore.RED + "   ⛔ AI TỪ CHỐI (Điểm thấp).")

            print("   💤 Waiting 60s...")
            time.sleep(60)

        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            print(Fore.RED + f"❌ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()