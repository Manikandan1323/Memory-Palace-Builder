import google.generativeai as genai
import os

model = None

def init_gemini(api_key=None):
    global model
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

def generate_palace_scene(prompt):
    if not model:
        raise RuntimeError("Gemini model not initialized. Call init_gemini(api_key) first.")
    response = model.generate_content(prompt)
    return response.text.strip()
