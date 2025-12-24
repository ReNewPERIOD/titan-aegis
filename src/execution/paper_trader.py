import csv
import os
import time
from colorama import Fore

class PaperTrader:
    def __init__(self, filename="trade_logs.csv"):
        self.filename = filename
        self.columns = ["Timestamp", "Symbol", "Action", "Price", "Volume", "TP", "SL", "Reason", "Score"]
        
        # Tạo file nếu chưa có
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(self.columns)

    def execute_order(self, symbol, action, price, tp, sl, reason, score, balance=1000):
        """
        Ghi lệnh vào sổ cái thay vì gửi lên sàn
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Tính Volume (Quản lý vốn Kelly đơn giản: 5% vốn)
        volume_usdt = balance * 0.05 
        volume_coin = volume_usdt / price
        
        log_entry = [timestamp, symbol, action, price, f"{volume_coin:.4f}", tp, sl, reason, score]
        
        # Ghi vào file
        try:
            with open(self.filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(log_entry)
                
            print(Fore.GREEN + "\n" + "="*50)
            print(Fore.GREEN + f"📝 ĐÃ KHỚP LỆNH PAPER TRADING: {action} {symbol}")
            print(f"   💵 Giá: {price} | Vol: {volume_usdt}$")
            print(f"   💾 Đã lưu vào file: {self.filename}")
            print("="*50 + "\n")
            return True
        except Exception as e:
            print(Fore.RED + f"❌ Lỗi ghi file: {e}")
            return False