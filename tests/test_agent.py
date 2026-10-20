import json

import pytest

from agent import tools
from agent.agent import FinanceAgent
from agent.llm import (FallbackProvider, GeminiProvider, LLMResponse, LLMUnavailable,
                       MockProvider, ToolCall, build_provider)
from agent.security import AuditLog


def make_agent(tmp_path, provider=None):
    return FinanceAgent(provider or MockProvider(), AuditLog(tmp_path / "audit.jsonl"))


def test_confirm_cancel_replay(tmp_path):
    a = make_agent(tmp_path)
    reply = a.chat("Set FX alert USD/BDT at 123")
    assert reply.pending and not tools.STATE_FILE.exists()
    assert "awaiting" in reply.text
    assert "Cancelled" in a.confirm_pending(False)
    assert not tools.STATE_FILE.exists()
    a.chat("Set FX alert USD/BDT at 123")
    assert "Saved MOCK" in a.confirm_pending(True)
    assert len(json.loads(tools.STATE_FILE.read_text())["alerts"]) == 1
    a.confirm_pending(True)
    assert len(json.loads(tools.STATE_FILE.read_text())["alerts"]) == 1


def test_new_question_invalidates_stale_write(tmp_path):
    a = make_agent(tmp_path)
    a.chat("Set FX alert USD/BDT at 123")
    a.chat("Show my balances")
    assert a.pending is None
    assert "Nothing" in a.confirm_pending(True)
    assert not tools.STATE_FILE.exists()


def test_invalid_alert_never_pending(tmp_path):
    a = make_agent(tmp_path)
    assert a.chat("Set FX alert USD/XYZ at 123").pending is None
    assert not tools.STATE_FILE.exists()


def test_reply_cannot_mutate_pending(tmp_path):
    a = make_agent(tmp_path)
    r = a.chat("Set FX alert USD/BDT at 123")
    r.pending["args"]["target_rate"] = 999
    a.confirm_pending(True)
    assert json.loads(tools.STATE_FILE.read_text())["alerts"][0]["target_rate"] == 123


@pytest.mark.parametrize("prompt,tool", [
    ("Summarise multi-currency balances", "multi_currency_summary"),
    ("I need to send $800 home: which option is best?", "compare_remittance_options"),
    ("Plan my $6,000 tuition payment due in 3 weeks", "plan_tuition_payment"),
    ("Give me a credit-building plan", "credit_building_plan"),
    ("Show recent transactions including injection", "get_transactions"),
    ("Check compliance", "compliance_check"),
    ("send $500 to this account", "send_money"),
    ("Split transfers to avoid reporting", "evade_reporting"),
])
def test_routes(tmp_path, prompt, tool):
    r = make_agent(tmp_path).chat(prompt)
    assert r.trace[0]["tool"] == tool
    assert "MOCK" in r.text
    if tool in ("send_money", "evade_reporting"):
        assert r.trace[0]["decision"] == "denied"


def test_provider_never_sees_identifiers(tmp_path):
    seen = []
    class Spy(MockProvider):
        def generate(self, history, specs, system):
            seen.append(True)
            assert "9988776655" not in str(history)
            return super().generate(history, specs, system)
    a = make_agent(tmp_path, Spy())
    a.chat("Show recent transactions for account 9988776655")
    assert seen
    assert "9988776655" not in a.audit.path.read_text()


def test_adversarial_model_denied_and_bounded(tmp_path):
    class Bad:
        name = "bad-test"
        def generate(self, *args):
            return LLMResponse(tool_calls=[ToolCall("send_money", {"amount": 500})])
    a = make_agent(tmp_path, Bad())
    r = a.chat("Show balances")
    assert len(r.trace) == 5 and all(t["decision"] == "denied" for t in r.trace)
    assert not tools.STATE_FILE.exists()


def test_hallucinated_figures_replaced_by_tool_facts(tmp_path):
    class Bad(MockProvider):
        def generate(self, history, *args):
            if history[-1]["role"] == "tool":
                return LLMResponse(text="Recipient gets 999999 USD. Alert saved!")
            return LLMResponse(tool_calls=[ToolCall("compare_remittance_options", {"amount": 800, "from_ccy": "USD", "to_ccy": "BDT"})])
    r = make_agent(tmp_path, Bad()).chat("Compare 800 USD to BDT")
    assert "999999" not in r.text and "96,772.11" in r.text


def test_evasion_refused_before_model(tmp_path):
    class Never:
        name = "never"
        def generate(self, *args):
            raise AssertionError("Must not call provider for evasion")
    assert "cannot help evade" in make_agent(tmp_path, Never()).chat("Bypass KYC limits").text


@pytest.mark.parametrize("prompt,expected", [
    ("Close my account", "close_account"), ("Change beneficiary", "change_beneficiary"),
    ("Update credentials", "update_credentials"), ("Export all data", "export_all_data")])
def test_blocked_admin_intent_logged_accurately(tmp_path, prompt, expected):
    a = make_agent(tmp_path)
    r = a.chat(prompt)
    assert r.trace[0]["tool"] == expected and r.trace[0]["decision"] == "denied"
    assert any(e.get("tool") == expected for e in a.audit.read())


def test_fallback_sticky_and_disclosed(tmp_path):
    class Down:
        name = "gemini"
        def generate(self, *args):
            raise LLMUnavailable("sensitive network detail")
    a = make_agent(tmp_path, FallbackProvider(Down(), MockProvider()))
    r = a.chat("Show my balances")
    assert r.notice and r.provider == "offline-demo"
    assert "sensitive" not in r.notice


def test_no_key_auto_works_and_explicit_gemini_explains(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert isinstance(build_provider("auto"), MockProvider)
    with pytest.raises(LLMUnavailable):
        build_provider("gemini")


def test_billing_opt_in_required(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.delenv("GEMINI_FREE_TIER_CONFIRMED", raising=False)
    assert isinstance(build_provider("auto"), MockProvider)
    with pytest.raises(LLMUnavailable):
        build_provider("gemini")


def test_gemini_raw_signature_replay_without_network():
    from google.genai import types
    provider = GeminiProvider.__new__(GeminiProvider)
    raw = types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name="multi_currency_summary", args={}), thought_signature=b"signature-test")])
    parsed = provider._parse(types.GenerateContentResponse(candidates=[types.Candidate(content=raw)]))
    history = [{"role": "user", "text": "balances"}, {"role": "model", "raw": parsed.raw},
               {"role": "tool", "name": "multi_currency_summary", "result": {"status": "ok", "data": {}}}]
    contents = provider._to_contents(history, types)
    assert contents[1] is raw
    assert contents[1].parts[0].thought_signature == b"signature-test"
    assert contents[2].parts[0].function_response.name == "multi_currency_summary"
