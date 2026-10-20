"""Intent routing for the no-key demo. Financial facts always come from tools."""
import json
import re
from datetime import timedelta

from .llm import LLMResponse, ToolCall


class CrossBorderMockProvider:
    name = "offline-demo"

    def generate(self, history, tools, system):
        results = []
        for h in reversed(history):
            if h["role"] != "tool":
                break
            results.append(h)
        if results:
            return LLMResponse(text="\n\n".join(self.compose(r) for r in reversed(results)))
        return self.route(history[-1]["text"] if history else "")

    def route(self, msg):
        from .tools import iso, load
        m = msg.lower()
        nums = [float(n.replace(",", "")) for n in re.findall(r"(?<![a-z])\d[\d,]*(?:\.\d+)?", m)]
        amount = nums[0] if nums else None
        def call(name, **args):
            return LLMResponse(tool_calls=[ToolCall(name, args)])
        if re.search(r"avoid|evade|bypass|circumvent|under the radar|without.*report", m) and re.search(r"report|limit|kyc|sanction|review|detect", m):
            return call("evade_reporting")
        if "alert" in m:
            pair = re.search(r"\b([a-z]{3})\s*[/_-]\s*([a-z]{3})\b", m)
            if not pair or amount is None:
                return LLMResponse(text="Specify a supported pair and target, e.g. set FX alert USD/BDT at 123.")
            return call("set_fx_alert", pair=f"{pair[1].upper()}/{pair[2].upper()}", target_rate=amount)
        if "tuition" in m:
            if amount is None:
                return LLMResponse(text="How much USD tuition is due and on which YYYY-MM-DD date?")
            explicit = re.search(r"\b20\d\d-\d\d-\d\d\b", m)
            weeks = re.search(r"(\d+)\s*weeks?", m)
            due = explicit[0] if explicit else (iso(load("profile.json")["as_of"]) + timedelta(weeks=int(weeks[1]) if weeks else 3)).isoformat()
            return call("plan_tuition_payment", amount_usd=amount, due_date=due)
        if "credit" in m:
            return call("credit_building_plan")
        if re.search(r"compliance|structur|suspicious|sanction|kyc|large.*transfer", m):
            return call("compliance_check")
        # Comparison intent precedes the money-movement catch so S2 stays a READ.
        if re.search(r"compar|which|best|option|cheapest|remittance", m):
            if amount is None:
                return LLMResponse(text="Give a total sender budget, e.g. compare 800 USD to BDT.")
            ccys = re.findall(r"\b(usd|bdt|eur|gbp|cny)\b", m)
            source, target = (ccys[0].upper(), ccys[1].upper()) if len(ccys) >= 2 else ("USD", "BDT")
            return call("compare_remittance_options", amount=amount, from_ccy=source, to_ccy=target)
        if re.search(r"\b(send|wire|pay|transfer)\b", m):
            return call("send_money", amount=amount or 0)
        if re.search(r"transaction|injection|recent|description", m):
            return call("get_transactions", limit=20)
        if re.search(r"summar|spend|balance|currenc|exposure|fee", m):
            return call("multi_currency_summary")
        return LLMResponse(text="I can compare remittances, plan tuition, summarise currencies, explain credit building, check compliance and prepare a confirmed sandbox FX alert. Try a sidebar example.")

    @staticmethod
    def compose(r):
        result = r["result"]
        if result["status"] == "denied":
            return "I cannot do that. " + result["reason"]
        if result["status"] == "pending_user_confirmation":
            return "FX alert prepared, awaiting your **Confirm** or **Cancel** button. Nothing is saved yet."
        if result["status"] == "error":
            return "Could not complete request: " + result["message"]
        d, name = result["data"], r["name"]
        if name == "compare_remittance_options":
            lines = [f"**MOCK comparison:** sender budget {d['amount']:,.2f} {d['from_ccy']}; mid-rate {d['mid_rate']:.6f} {d['to_ccy']}/{d['from_ccy']}.", d["method"]]
            for o in d["options"]:
                lines.append(f"- **{o['provider']}**: recipient {o['recipient_amount']:,.2f} {d['to_ccy']}; fee {o['fee_sender']:.2f} {d['from_ccy']}; margin {o['fx_margin_pct']}%; total cost {o['total_cost_pct']}%; {o['speed_hours']}h. {o['arithmetic']}")
            return "\n".join(lines + [d["hidden_margin_trap"]])
        if name == "plan_tuition_payment":
            lines = [f"**MOCK tuition USD {d['amount_usd']:,.2f}, due {d['due_date']}**", d["recommendation"]]
            for o in d["options"]:
                lines.append(f"- {o['provider']}: BDT {o['sender_bdt']:,.2f}; fee BDT {o['fee_bdt']:,.2f}; margin {o['fx_margin_pct']}%; total cost {o['total_cost_pct']}%; with 2% reserve BDT {o['with_2pct_buffer_bdt']:,.2f}; {o['speed_hours']}h; start by {o['latest_start']}. {o['arithmetic']}")
            return "\n".join(lines + [f"30-day BDT/USD change: {d['trend_30day_pct']}%.", d["timing"], d["buffer"], d["risk_options"], d["affordability"]])
        if name == "credit_building_plan":
            return "**Newcomer credit plan**\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(d["steps"], 1)) + "\n" + d["limitation"]
        if name == "compliance_check":
            return "**MOCK compliance review**\n" + "\n".join(f"- {f['type']}: {f['reason']} IDs: {', '.join(f['ids'])}" for f in d["flags"]) + "\n" + "\n".join(d[k] for k in ("threshold_note", "guidance", "kyc_sanctions"))
        if name == "multi_currency_summary":
            return "**MOCK multi-currency summary**\n" + "\n".join(f"- {r['currency']}: balance {r['balance']:,.2f}; spend {r['spend']:,.2f}; FX fees {r['fx_fees']:,.2f}." for r in d["by_currency"]) + f"\nTotal home value BDT {d['total_home_bdt']:,.2f}; USD exposure {d['usd_exposure_pct']}%.\n" + d["high_card_fee"] + "\n" + d["method"]
        if name == "get_transactions":
            return "**MOCK transactions (masked and sanitised)**\n" + "\n".join(f"- {t['date']} | {t['description']} | {t['amount']} {t['currency']} | {t['account']}" for t in d["transactions"]) + "\nNeutralised description IDs: " + str(d["security_flags"]["suspicious_descriptions_neutralised"])
        return json.dumps(d, indent=2)
