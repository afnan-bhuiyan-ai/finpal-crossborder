"""Security layer: PII masking, prompt-injection defence, permission tiers, audit log.

Design principle: the LLM is NOT trusted. Every tool call it proposes passes through
PolicyEngine, and every piece of data it reads is sanitised first.
"""
import json
import math
import os
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from .config import LOG_DIR, MAX_TOOL_CALLS_PER_TURN, MAX_USER_CHARS

# ---------- permission tiers ----------
READ = "read"        # auto-allowed, no side effects
WRITE = "write"      # changes sandbox state -> needs explicit human confirmation
BLOCKED = "blocked"  # never allowed for the agent

# Money-movement / credential actions deliberately do not exist as tools. If a model
# (or an injected instruction) asks for one, the policy engine denies and logs it.
BLOCKED_ACTIONS = {
    "transfer_money", "make_payment", "send_payment", "pay_bill", "withdraw",
    "close_account", "change_password", "update_credentials", "export_all_data",
    "send_money", "wire_transfer", "change_beneficiary", "evade_reporting",
}

DISCLAIMER = "_MOCK sandbox data, rates and fees. General education, not financial/legal advice._"

# ---------- masking ----------
_LONG_NUM = re.compile(r"(?<![\d.])\d{9,19}(?![\d.])")
_EMAIL = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
_SECRET = re.compile(r"(?:AIza[A-Za-z0-9_-]{20,}|(?:sk-|Bearer\s+)[A-Za-z0-9_-]{12,})")
_SEPARATED = re.compile(r"(?<!\d)\d(?:[ -]?\d){8,18}(?!\d)")


def mask_numbers(text: str) -> str:
    """Mask account/card-like numbers (9-19 digits) keeping the last 4, and e-mail local parts."""
    text = _LONG_NUM.sub(lambda m: "*" * (len(m.group()) - 4) + m.group()[-4:], text)
    text = _SEPARATED.sub(lambda m: "[MASKED identifier]" if re.search(r"[ -]", m.group()) else m.group(), text)
    text = _SECRET.sub("[REDACTED secret]", text)
    return _EMAIL.sub(lambda m: m.group(1) + "***" + m.group(2), text)


def mask_deep(obj):
    if isinstance(obj, str):
        return mask_numbers(obj)
    if isinstance(obj, dict):
        return {k: "[REDACTED]" if re.search(r"password|secret|api.?key|credential|token", str(k), re.I) else mask_deep(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [mask_deep(v) for v in obj]
    return obj


def mask_account(number: str) -> str:
    return "****" + str(number)[-4:]


# ---------- prompt-injection defence ----------
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|any\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+.{0,40}(instructions?|rules?|prompt)",
    r"(reveal|show|print|leak)\s+.{0,30}(system prompt|api key|password|secret)",
    r"you\s+are\s+now\s+",
    r"</?\s*(system|assistant|developer)\s*>",
    r"\b(transfer|send|wire|pay)\b.{0,40}(\$|usd|eur)?\s?\d[\d,.]*\s*(to|into)?\s*(account|acct|iban)?",
]
_INJECTION_RE = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def sanitize_untrusted(text: str):
    """Neutralise instruction-like text inside untrusted data. Returns (clean_text, was_flagged)."""
    if any(rx.search(text) for rx in _INJECTION_RE):
        return "[REDACTED: instruction-like description]", True
    return mask_numbers(text[:300]), False


def guard_user_input(text: str) -> str:
    """Length-limit, strip control characters and mask account numbers before the LLM sees the text."""
    text = (text or "").strip()[:MAX_USER_CHARS]
    text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\t")
    return mask_numbers(text)


# ---------- policy engine ----------
@dataclass
class Decision:
    status: str   # "allowed" | "needs_confirmation" | "denied"
    reason: str = ""

    @property
    def allowed(self):
        return self.status == "allowed"


class PolicyEngine:
    def __init__(self, registry, max_calls_per_turn=MAX_TOOL_CALLS_PER_TURN):
        self.registry = registry
        self.max_calls = max_calls_per_turn

    def decide(self, name, args, calls_so_far=0, confirmed=False) -> Decision:
        if name in BLOCKED_ACTIONS:
            return Decision("denied", f"'{name}' is a blocked action: this agent can never move money or change credentials.")
        spec = self.registry.get(name)
        if spec is None:
            return Decision("denied", f"Unknown tool '{name}' (not on the allow-list).")
        if not isinstance(args, dict):
            return Decision("denied", "Tool arguments must be an object.")
        extra = set(args) - set(spec.parameters.get("properties", {}))
        if extra:
            return Decision("denied", f"Unexpected arguments rejected: {sorted(extra)}")
        missing = set(spec.parameters.get("required", [])) - set(args)
        if missing:
            return Decision("denied", f"Missing required arguments: {sorted(missing)}")
        for key, value in args.items():
            kind = spec.parameters["properties"][key].get("type")
            valid = ((kind == "string" and isinstance(value, str) and len(value) <= 100)
                     or (kind == "integer" and type(value) is int)
                     or (kind == "number" and type(value) in (int, float) and math.isfinite(value)))
            if not valid:
                return Decision("denied", f"Invalid argument type or size: {key}")
        if calls_so_far >= self.max_calls:
            return Decision("denied", f"Per-turn tool-call limit ({self.max_calls}) reached.")
        if spec.tier == BLOCKED:
            return Decision("denied", f"Tool '{name}' is blocked.")
        if spec.tier == WRITE and not confirmed:
            return Decision("needs_confirmation", f"'{name}' changes account state and needs the user's explicit confirmation.")
        return Decision("allowed", "ok")


# ---------- audit log ----------
class AuditLog:
    """Append-only JSONL audit trail of every message, tool call, decision and result."""

    def __init__(self, path=None, session_id=None):
        self.path = Path(path) if path else Path(os.getenv("FINPAL_AUDIT_FILE", str(LOG_DIR / "audit.jsonl")))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.session_id = session_id or uuid.uuid4().hex[:8]

    def log(self, event, **details):
        record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "session": self.session_id,
                  "event": event, **mask_deep(details)}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

    def read(self, last=50):
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-last:]
        return [r for line in lines if line.strip() for r in [json.loads(line)] if r.get("session") == self.session_id]
