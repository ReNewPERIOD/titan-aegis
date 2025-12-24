import os
import json
import time
from google import genai
from google.genai import types
from colorama import Fore

# Fallback import
try:
    from ai.prompts import RISK_MANAGER_PROMPT
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.ai.prompts import RISK_MANAGER_PROMPT

class TitanJudge:
    def __init__(self, api_key=None):
        # API Key của bạn (Đã chèn sẵn)
        self.api_key = api_key or "AIzaSyAPhz98e2N8s-yCK8Fyw0K677f3U8KH_a8"
        
        if not self.api_key:
            print(Fore.RED + "⚠️ CẢNH BÁO: Chưa có API Key.")
            return

        self.client = genai.Client(api_key=self.api_key)
        
        # --- THAY ĐỔI QUAN TRỌNG ---
        # Dùng 'gemini-flash-latest' thay vì 2.0 để tránh bị nghẽn mạng (429)
        # Model này trỏ tới bản Flash ổn định nhất hiện tại (thường là 1.5)
        self.model_name = "gemini-flash-latest" 

    def evaluate(self, market_data, math_results, news_summary="Không có tin tức đặc biệt."):
        final_prompt = RISK_MANAGER_PROMPT.format(
            market_data=json.dumps(market_data),
            math_results=json.dumps(math_results),
            news_context=news_summary
        )

        # Thử tối đa 3 lần
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=final_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                
                if response.text:
                    return json.loads(response.text)
                else:
                    raise ValueError("Empty response")

            except Exception as e:
                error_msg = str(e)
                # Xử lý lỗi quá tải (429)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    wait_time = (attempt + 1) * 3 # Giảm thời gian chờ xuống 3s cho nhanh
                    print(Fore.YELLOW + f"⚠️ Mạng bận. Thử lại sau {wait_time}s... (Lần {attempt+1})")
                    time.sleep(wait_time)
                else:
                    print(Fore.RED + f"❌ Lỗi AI ({self.model_name}): {e}")
                    return {
                        "decision": "ERROR", 
                        "score": 0, 
                        "reason": f"Connection Failed: {str(e)}",
                        "risk_flags": ["API Error"]
                    }
        
        return {"decision": "REJECT", "score": 0, "reason": "Timeout", "risk_flags": ["Overload"]}