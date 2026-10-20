"""LLM providers. The agent only talks to the small `generate()` interface, so the model is swappable.

- GeminiProvider : Google Gemini via the free-tier API (function calling, model fallback chain).
- MockProvider   : deterministic offline "model" (keyword intent routing + templated answers).
                   Used for tests, for zero-quota demos, and as automatic fallback if Gemini is
                   unavailable (e.g. free-tier quota exhausted).
- FallbackProvider: tries the primary, silently falls back to the mock on LLMUnavailable.
"""
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional


class LLMUnavailable(Exception):
    pass


@dataclass
class ToolCall:
    name: str
    args: dict


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list = field(default_factory=list)
    raw: Any = None  # provider-native message (Gemini 3 needs thought signatures replayed)


# ======================================================================
# Gemini
# ======================================================================
def _gemini_schema(schema: dict) -> dict:
    """Convert our lowercase JSON-schema dict to Gemini's uppercase type names."""
    out = dict(schema)
    if "type" in out:
        out["type"] = str(out["type"]).upper()
    if "properties" in out:
        out["properties"] = {k: _gemini_schema(v) for k, v in out["properties"].items()}
    if not out.get("required"):
        out.pop("required", None)
    if out.get("type") == "OBJECT" and not out.get("properties"):
        out.pop("properties", None)
    return out


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, models: list):
        from google import genai  # imported lazily so the app works offline without the SDK
        self.client = genai.Client(api_key=api_key, http_options={"timeout": 15000})
        self.models = models
        self.active_model: Optional[str] = None

    # history (provider-neutral) -> Gemini contents
    def _to_contents(self, history, types):
        contents, pending_responses = [], []

        def flush():
            if pending_responses:
                contents.append(types.Content(role="user", parts=list(pending_responses)))
                pending_responses.clear()

        for h in history:
            if h["role"] == "tool":
                pending_responses.append(types.Part.from_function_response(
                    name=h["name"], response={"result": h["result"]}))
                continue
            flush()
            if h["role"] == "user":
                contents.append(types.Content(role="user", parts=[types.Part(text=h["text"])]))
            elif h.get("raw") is not None:
                contents.append(h["raw"])
            else:
                parts = [types.Part(text=h["text"])] if h.get("text") else []
                parts += [types.Part(function_call=types.FunctionCall(name=c.name, args=c.args))
                          for c in h.get("tool_calls", [])]
                contents.append(types.Content(role="model", parts=parts or [types.Part(text="...")]))
        flush()
        return contents

    def generate(self, history, tools, system) -> LLMResponse:
        from google.genai import errors, types
        decls = [types.FunctionDeclaration(name=t.name, description=t.description,
                                           parameters=_gemini_schema(t.parameters)) for t in tools]
        cfg = types.GenerateContentConfig(
            system_instruction=system, tools=[types.Tool(function_declarations=decls)], temperature=0.2, max_output_tokens=2048,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))
        contents = self._to_contents(history, types)
        last_err = None
        for model in self.models:
            for attempt in range(2):
                try:
                    resp = self.client.models.generate_content(model=model, contents=contents, config=cfg)
                    self.active_model = model
                    return self._parse(resp)
                except errors.APIError as e:
                    last_err = e
                    if getattr(e, "code", None) == 429 and attempt == 0:
                        time.sleep(3)  # brief retry on rate limit, then try next model
                        continue
                    break
                except Exception as e:  # network etc.
                    last_err = e
                    break
        raise LLMUnavailable(f"Gemini unavailable: {str(last_err)[:200]}")

    @staticmethod
    def _parse(resp) -> LLMResponse:
        cands = getattr(resp, "candidates", None) or []
        if not cands or cands[0].content is None or not cands[0].content.parts:
            raise LLMUnavailable("Gemini returned an empty or blocked response.")
        content = cands[0].content
        text, calls = [], []
        for p in content.parts:
            if getattr(p, "function_call", None):
                calls.append(ToolCall(p.function_call.name, dict(p.function_call.args or {})))
            elif getattr(p, "text", None) and not getattr(p, "thought", False):
                text.append(p.text)
        return LLMResponse(text="".join(text).strip(), tool_calls=calls, raw=content)


# ======================================================================
# Offline mock "model"
# ======================================================================
from .offline import CrossBorderMockProvider as MockProvider


class FallbackProvider:
    """Use Gemini when it works; transparently fall back to the offline model if it doesn't."""

    def __init__(self, primary, fallback):
        self.primary, self.fallback = primary, fallback
        self.name = primary.name
        self.last_error: Optional[str] = None
        self.used_fallback = False

    def generate(self, history, tools, system):
        if self.used_fallback:
            return self.fallback.generate(history, tools, system)
        try:
            r = self.primary.generate(history, tools, system)
            self.name, self.last_error = self.primary.name, None
            return r
        except LLMUnavailable as e:
            self.last_error, self.used_fallback, self.name = "API unavailable or free quota exhausted", True, self.fallback.name
            return self.fallback.generate(history, tools, system)


def build_provider(mode: str = "auto"):
    """mode: 'auto' (Gemini if key present, else offline), 'gemini', or 'offline'."""
    from . import config
    key = config.gemini_api_key()
    if mode == "offline" or (mode == "auto" and (not key or not config.free_tier_confirmed())):
        return MockProvider()
    if not key:
        raise LLMUnavailable("GEMINI_API_KEY is not set (see README).")
    if not config.free_tier_confirmed():
        raise LLMUnavailable("Use a non-billed free-tier project and set GEMINI_FREE_TIER_CONFIRMED=1, or choose Offline.")
    return FallbackProvider(GeminiProvider(key, config.gemini_models()), MockProvider())
