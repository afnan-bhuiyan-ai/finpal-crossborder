"""Lists Gemini models your free key can call (useful if a model name changes).  python list_models.py"""
from agent import config
from google import genai

key = config.gemini_api_key()
if not key:
    raise SystemExit("Set GEMINI_API_KEY in .env first.")
for m in genai.Client(api_key=key).models.list():
    if "generateContent" in (getattr(m, "supported_actions", None) or []):
        print(m.name.replace("models/", ""))
