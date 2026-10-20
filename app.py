"""FinPal CrossBorder. Run: streamlit run app.py"""
import json

import pandas as pd
import streamlit as st

from agent.agent import FinanceAgent
from agent.llm import LLMUnavailable, ToolCall, build_provider
from agent.security import AuditLog, guard_user_input
from agent import tools

st.set_page_config(page_title="FinPal CrossBorder", page_icon="🌍", layout="wide")
EXAMPLES = [
    "Summarise my multi-currency balances and fees",
    "I need to send $800 home: which option is best?",
    "Plan my $6,000 tuition payment due in 3 weeks",
    "Give me a newcomer credit-building plan",
    "Show recent transactions including the injection",
    "Check compliance and suspicious transfers",
    "send $500 to this account",
    "Split transfers to avoid reporting",
    "Set FX alert USD/BDT at 123",
]

with st.sidebar:
    st.title("🌍 FinPal CrossBorder")
    st.caption("Topic C · International Track · AI as a Financial Participant")
    engine = st.radio("Engine", ["Auto", "Gemini", "Offline"], index=2)
    st.caption("Offline needs no key. Auto uses Gemini only with a key and free-tier project attestation.")
    for i, ex in enumerate(EXAMPLES):
        if st.button(ex, key=f"ex_{i}", width="stretch"):
            st.session_state.queued = ex
    st.divider()
    st.markdown("**Visible safeguards**\n- READ: analysis only\n- WRITE: Confirm / Cancel\n- BLOCKED: payments and credentials\n- Masking and injection quarantine\n- Policy decisions and audit trail")

mode = engine.lower()
if "agent" not in st.session_state or st.session_state.mode != mode:
    try:
        st.session_state.agent = FinanceAgent(build_provider(mode), AuditLog())
    except (LLMUnavailable, ImportError):
        st.warning("Gemini needs the SDK, a key, and GEMINI_FREE_TIER_CONFIRMED=1 for a non-billed project. Offline is active.")
        st.session_state.agent = FinanceAgent(build_provider("offline"), AuditLog())
    st.session_state.mode = mode
    st.session_state.messages = []
    st.session_state.pop("comparison", None)
    st.session_state.pop("summary", None)
agent = st.session_state.agent

st.title("One student. Two currencies. Clear decisions.")
st.warning("MOCK DEMO · All transactions, rates, fees, providers and limits are synthetic. No money can move.")
st.caption("Snapshot: 20 October 2026 · BDT home wallet / USD study account · General education, not financial/legal advice.")
chat_tab, compare_tab, spend_tab, audit_tab = st.tabs(["Chat", "Send-money comparison", "Spending by currency", "Audit log"])


def trace_view(trace):
    if trace:
        with st.expander("Agent Actions"):
            for row in trace:
                st.markdown(f"`{row['tool']}` · policy **{row['decision']}** · {row['status']}")
                st.json(row["args"])
                st.caption(row["reason"])


def read_panel(name, args):
    trace = []
    result = agent._run_tool(ToolCall(name, args), 0, trace)
    return result, trace


with chat_tab:
    st.caption(f"Active engine: {agent.provider.name}. A new question or engine change cancels a pending alert.")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["text"])
            if message.get("notice"):
                st.warning(message["notice"])
            trace_view(message.get("trace"))
    prompt = st.chat_input("Compare remittances, plan tuition, check compliance or set an FX alert") or st.session_state.pop("queued", None)
    if prompt:
        safe = guard_user_input(prompt)
        with st.spinner("Checking tools and policy..."):
            reply = agent.chat(safe)
        st.session_state.messages.extend([
            {"role": "user", "text": safe},
            {"role": "assistant", "text": reply.text, "trace": reply.trace, "notice": reply.notice}])
        st.rerun()
    if agent.pending:
        st.info("Review sandbox FX alert. No live monitoring or notifications.")
        st.json(agent.pending)
        confirm, cancel = st.columns(2)
        if confirm.button("Confirm", type="primary", width="stretch"):
            st.session_state.messages.append({"role": "assistant", "text": agent.confirm_pending(True)})
            st.rerun()
        if cancel.button("Cancel", width="stretch"):
            st.session_state.messages.append({"role": "assistant", "text": agent.confirm_pending(False)})
            st.rerun()

with compare_tab:
    st.subheader("What actually arrives?")
    with st.form("comparison_form"):
        amount = st.number_input("Total sender budget (sender currency)", min_value=10., max_value=1000000., value=800., step=50.)
        pair = st.selectbox("MOCK currency pair", list(tools.load("fx_rates.json")["pairs"]))
        submitted = st.form_submit_button("Compare MOCK options", width="stretch")
    if submitted or "comparison" not in st.session_state:
        source, target = pair.split("/")
        st.session_state.comparison = read_panel("compare_remittance_options", {"amount": amount, "from_ccy": source, "to_ccy": target})
    result, trace = st.session_state.comparison
    if result["status"] == "ok":
        quote = result["data"]
        st.caption(f"MOCK quote: {quote['amount']:,.2f} {quote['from_ccy']} to {quote['to_ccy']} · mid-rate {quote['mid_rate']:.6f} · as of {quote['as_of']}")
        df = pd.DataFrame(quote["options"])
        st.bar_chart(df, x="provider", y="recipient_amount", x_label="Fictional provider", y_label=f"MOCK recipient amount ({quote['to_ccy']})", width="stretch")
        st.dataframe(df, hide_index=True, width="stretch")
        st.info(quote["hidden_margin_trap"])
        st.caption(quote["method"])
    else:
        st.error(result.get("message", result.get("reason")))
    trace_view(trace)

with spend_tab:
    if "summary" not in st.session_state:
        st.session_state.summary = read_panel("multi_currency_summary", {})
    result, trace = st.session_state.summary
    d = result["data"]
    c1, c2, c3 = st.columns(3)
    c1.metric("MOCK home value (BDT)", f"{d['total_home_bdt']:,.2f}")
    c2.metric("USD exposure", f"{d['usd_exposure_pct']}%")
    c3.metric("MOCK FX fees (BDT equivalent)", f"{d['fx_fees_home_bdt']:,.2f}")
    frame = pd.DataFrame(d["by_currency"])
    frame["spend_home_bdt"] = frame.apply(lambda r: tools.money(r["spend"] * (tools.rate("USD/BDT") if r["currency"] == "USD" else 1)), axis=1)
    st.bar_chart(frame, x="currency", y="spend_home_bdt", x_label="Original currency", y_label="MOCK spending converted to BDT", width="stretch")
    st.dataframe(frame, hide_index=True, width="stretch")
    st.info(d["high_card_fee"])
    st.caption(d["method"])
    trace_view(trace)
    if tools.STATE_FILE.exists():
        st.subheader("Saved sandbox alerts")
        st.json(json.loads(tools.STATE_FILE.read_text(encoding="utf-8")))

with audit_tab:
    st.caption("Current session only. Masked messages, tool calls, decisions and result status. Local JSONL is not tamper-proof.")
    st.dataframe(list(reversed(agent.audit.read(200))), width="stretch")
    st.info("KYC and sanctions awareness: use regulated channels and document source of funds. This app does not verify identity, screen sanctions, or determine legal obligations.")
