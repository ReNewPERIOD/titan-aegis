import os
from google import genai

# ==========================================
# 👇 DÁN API KEY CỦA BẠN VÀO GIỮA 2 DẤU NHÁY DƯỚI ĐÂY
# Ví dụ: MY_API_KEY = "AIzaSyDxxxxxxxxxxxx"
MY_API_KEY = "AIzaSyAPhz98e2N8s-yCK8Fyw0K677f3U8KH_a8"
# ==========================================

def get_models():
    # Kiem tra xem da dan key chua
    if "PASTE" in MY_API_KEY:
        print("ERROR: Please paste your API Key in line 7 first!")
        return

    print("... Connecting to Google ...")
    
    try:
        client = genai.Client(api_key=MY_API_KEY)
        
        # Lay danh sach model (List models)
        # Pager object iterable
        models_pager = client.models.list()
        
        print("\n--- AVAILABLE MODELS ---")
        found = False
        for m in models_pager:
            # Chi in ra cac model Gemini
            if "gemini" in m.name:
                print(f"ID: {m.name}")
                found = True
                
        if not found:
            print("No Gemini models found. Check your API Key permissions.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    get_models()