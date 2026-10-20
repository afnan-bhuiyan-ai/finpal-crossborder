import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv is optional
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "logs"
EVIDENCE_DIR = ROOT / "evidence"
if load_dotenv:
    load_dotenv(ROOT / ".env")

CURRENCY = "USD"
MAX_USER_CHARS = 2000
MAX_TOOL_CALLS_PER_TURN = 6
MAX_AGENT_STEPS = 5


def gemini_api_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key if key and key != "your_key_here" else None


def gemini_models():
    raw = os.getenv("GEMINI_MODELS", "gemini-flash-lite-latest,gemini-flash-latest")
    return [m.strip() for m in raw.split(",") if m.strip()]


def free_tier_confirmed():
    """Operator attests project has no billing. API cannot prove this from a key."""
    return os.getenv("GEMINI_FREE_TIER_CONFIRMED", "0") == "1"
