import os
import sys
# Setup đường dẫn
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.gemini_client import TitanJudge
from colorama import Fore, init

init(autoreset=True)

def run_test():
    print(Fore.CYAN + "🧠 TITAN AEGIS: Đang kết nối não bộ AI...")
    
    # --- CẤU HÌNH API KEY TẠM THỜI ---
    # Hãy thay chuỗi này bằng API Key bạn vừa lấy ở Bước 1
    # Sau này chúng ta sẽ đưa vào file .env cho bảo mật
    MY_API_KEY = "AIzaSyAPhz98e2N8s-yCK8Fyw0K677f3U8KH_a8" 
    
    if MY_API_KEY == "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY":
        print(Fore.RED + "❌ BẠN CHƯA DÁN API KEY VÀO FILE CODE!")
        return

    judge = TitanJudge(api_key=MY_API_KEY)

    # --- TÌNH HUỐNG GIẢ ĐỊNH ---
    print(Fore.YELLOW + "\n--- TÌNH HUỐNG: KÈO NGON NHƯNG TIN XẤU ---")
    
    # 1. Toán học bảo ngon (Winrate cao)
    math_results = {
        "win_probability": 85.5,
        "ruin_probability": 2.1,
        "risk_score": 9
    }
    
    # 2. Nhưng Tin tức lại xấu (FUD)
    bad_news = "BREAKING: SEC vừa khởi kiện sàn Binance. Thị trường hoảng loạn bán tháo."
    
    market_data = {"symbol": "BTC/USDT", "price": 65000, "trend": "UP"}

    print(f"📊 Toán học: {math_results['win_probability']}% Win")
    print(f"📰 Tin tức: {bad_news}")
    print("⏳ AI đang suy nghĩ...")

    # 3. Phán quyết
    verdict = judge.evaluate(market_data, math_results, bad_news)
    
    print("-" * 30)
    print(f"🤖 QUYẾT ĐỊNH: {Fore.GREEN if verdict['score'] > 10 else Fore.RED}{verdict['decision']}")
    print(f"points ĐIỂM SỐ:   {verdict['score']}/15")
    print(f"🗣️ LÝ DO:     {verdict['reason']}")
    print(f"🚩 CỜ RỦI RO: {verdict.get('risk_flags')}")
    print("-" * 30)

if __name__ == "__main__":
    run_test()