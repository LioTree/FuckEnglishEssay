import google.generativeai as genai
import os

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Model Name: {m.name}")
        print(f"Display Name: {m.display_name}")  # 可选：显示更友好的名称
        print(f"Supported Methods: {m.supported_generation_methods}")
        print("---")
