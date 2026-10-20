"""Deterministic MOCK calculations. No bank, FX or payment network access."""
import csv
import json
import math
import os
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Callable

from . import config
from .security import READ, WRITE, mask_account, sanitize_untrusted


class ToolError(ValueError):
    pass


STATE_FILE = Path(os.getenv("FINPAL_STATE_FILE", str(config.LOG_DIR / "sandbox_state.json")))
MOCK = "MOCK synthetic data, rates, fees and limits; not financial/legal advice."


def load(name):
    return json.loads((config.DATA_DIR / name).read_text(encoding="utf-8"))


def money(x):
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def number(x, field, low=.01, high=1000000):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not low <= x <= high:
        raise ToolError(f"{field} must be a finite number between {low} and {high}.")
    return float(x)


def iso(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ToolError("Date must be YYYY-MM-DD.")


def rate(pair):
    pairs = load("fx_rates.json")["pairs"]
    if pair not in pairs:
        raise ToolError("Unsupported pair; see data/fx_rates.json.")
    return pairs[pair]["mid_rate"]


def load_transactions():
    with (config.DATA_DIR / "transactions.csv").open(newline="", encoding="utf-8") as f:
        return [{**r, "amount": float(r["amount"]), "fx_fee": float(r["fx_fee"])} for r in csv.DictReader(f)]


def get_transactions(start_date=None, end_date=None, category=None, currency=None, limit=20):
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ToolError("limit must be an integer from 1 to 50.")
    start, end = iso(start_date) if start_date else None, iso(end_date) if end_date else None
    if start and end and start > end:
        raise ToolError("start_date must precede end_date.")
    if currency and currency not in ("USD", "BDT"):
        raise ToolError("Transaction currency must be USD or BDT.")
    rows = [r for r in load_transactions() if
            (not start or iso(r["date"]) >= start) and (not end or iso(r["date"]) <= end)
            and (not category or r["category"].lower() == category.lower()) and (not currency or r["currency"] == currency)]
    rows.sort(key=lambda r: (r["date"], r["id"]), reverse=True)
    clean, flagged = [], []
    for r in rows[:limit]:
        desc, flag = sanitize_untrusted(r["description"])
        clean.append({**r, "description": desc, "account": mask_account(r["account"])})
        if flag:
            flagged.append(r["id"])
    return {"disclosure": MOCK, "total_matching": len(rows), "transactions": clean,
            "security_flags": {"suspicious_descriptions_neutralised": flagged}}


def multi_currency_summary():
    profile, txns = load("profile.json"), load_transactions()
    rows = []
    for ccy, opening in profile["opening_balances"].items():
        subset = [t for t in txns if t["currency"] == ccy]
        balance = money(opening + sum(t["amount"] for t in subset))
        rows.append({"currency": ccy, "opening_balance": opening, "balance": balance,
                     "income": money(sum(t["amount"] for t in subset if t["amount"] > 0)),
                     "outflow": money(-sum(t["amount"] for t in subset if t["amount"] < 0)),
                     "spend": money(-sum(t["amount"] for t in subset if t["amount"] < 0 and t["category"] != "Transfer")),
                     "fx_fees": money(sum(t["fx_fee"] for t in subset)),
                     "home_value": money(balance * (rate("USD/BDT") if ccy == "USD" else 1))})
    total = money(sum(r["home_value"] for r in rows))
    usd = next(r for r in rows if r["currency"] == "USD")
    return {"disclosure": MOCK, "as_of": profile["as_of"], "by_currency": rows, "total_home_bdt": total,
            "usd_exposure_pct": money(100 * usd["home_value"] / total),
            "fx_fees_home_bdt": money(sum(r["fx_fees"] * (rate("USD/BDT") if r["currency"] == "USD" else 1) for r in rows)),
            "high_card_fee": "MOCK USD 28 fee / USD 400 purchase = 7%; review card terms.",
            "method": "Closing = opening + signed transactions. Transfers excluded from spending; included in outflows. Snapshot FX, not historical valuation."}


def compare_remittance_options(amount, from_ccy, to_ccy):
    amount = number(amount, "amount")
    mid = rate(f"{from_ccy}/{to_ccy}")
    options = []
    for p in load("providers.json")["providers"]:
        if not p["min_amount"] <= amount <= p["max_amount"]:
            continue
        fee = money(p["fixed_fee"] + amount * p["percentage_fee"] / 100)
        if fee >= amount:
            continue
        effective = mid * (1 - p["fx_margin_pct"] / 100)
        received = money((amount - fee) * effective)
        options.append({"provider": p["name"], "fee_sender": fee, "fx_margin_pct": p["fx_margin_pct"],
                        "effective_rate": effective, "recipient_amount": received,
                        "cost_sender": money(amount - received / mid),
                        "total_cost_pct": money(100 * (amount - received / mid) / amount), "speed_hours": p["speed_hours"],
                        "arithmetic": f"({amount} - {fee}) * {effective:.10f} = {received} {to_ccy}"})
    if not options:
        raise ToolError("No MOCK provider supports that amount after fees and limits.")
    options.sort(key=lambda r: (-r["recipient_amount"], r["speed_hours"]))
    return {"disclosure": MOCK, "as_of": load("fx_rates.json")["as_of"], "amount": amount,
            "from_ccy": from_ccy, "to_ccy": to_ccy, "mid_rate": mid, "options": options,
            "method": "Amount is total sender budget; fees deducted before FX. Cost includes fee and FX margin. Limits are in sender currency.",
            "hidden_margin_trap": "ZeroFee Mirage has no explicit fee but takes 4% in its MOCK rate. Compare recipient amount, not advertised fee."}


def plan_tuition_payment(amount_usd, due_date):
    target = number(amount_usd, "amount_usd", 1, 100000)
    due, today = iso(due_date), iso(load("profile.json")["as_of"])
    if not today < due <= today + timedelta(days=365):
        raise ToolError("Due date must be after the MOCK as-of date and within 365 days.")
    mid = rate("BDT/USD")
    hist = load("fx_rates.json")["pairs"]["BDT/USD"]["history"]
    change = 100 * (hist[-1]["rate"] / hist[0]["rate"] - 1)
    options = []
    for p in load("providers.json")["providers"]:
        effective = mid * (1 - p["fx_margin_pct"] / 100)
        budget = math.ceil((target / effective + p["fixed_fee"]) / (1 - p["percentage_fee"] / 100) * 100) / 100
        while money((budget - money(p["fixed_fee"] + budget * p["percentage_fee"] / 100)) * effective) < target:
            budget = money(budget + .01)
        latest = due - timedelta(days=math.ceil(p["speed_hours"] / 24) + 2)
        if p["min_amount"] <= budget <= p["max_amount"] and latest >= today:
            options.append({"provider": p["name"], "sender_bdt": budget,
                            "fee_bdt": money(p["fixed_fee"] + budget * p["percentage_fee"] / 100),
                            "fx_margin_pct": p["fx_margin_pct"], "effective_rate": effective,
                            "cost_bdt": money(budget - target / mid), "total_cost_pct": money(100 * (budget - target / mid) / budget),
                            "with_2pct_buffer_bdt": money(budget * 1.02), "speed_hours": p["speed_hours"],
                            "latest_start": latest.isoformat(),
                            "arithmetic": f"(BDT budget - rounded fee) * {effective:.10f} >= USD {target}"})
    if not options:
        raise ToolError("No MOCK provider meets deadline and limits; contact the university through verified channels.")
    options.sort(key=lambda r: r["sender_bdt"])
    balances = {r["currency"]: r["balance"] for r in multi_currency_summary()["by_currency"]}
    covered = balances["USD"] >= target
    gap = money(max(0, options[0]["sender_bdt"] - balances["BDT"]))
    existing = {"available_usd": balances["USD"], "covers_tuition_before_other_obligations": covered,
                "modeled_fx_cost_usd": 0, "payment_fees": "Unknown; verify university/channel terms"}
    return {"disclosure": MOCK, "as_of": today.isoformat(), "amount_usd": target, "due_date": due.isoformat(),
            "mid_rate_bdt_usd": mid, "trend_30day_pct": money(change), "options": options[:3],
            "existing_usd_option": existing,
            "recommendation": (("Existing MOCK USD balance covers tuition before other obligations: compare the university's accepted USD funding channel first. No FX conversion is needed; payment fees and delivery time are unknown. " if covered else "Existing MOCK USD balance does not cover full tuition. ") + f"Among BDT conversion options, {options[0]['provider']} is lowest-cost. Start by {options[0]['latest_start']}; allow two calendar days beyond provider speed for reconciliation."),
            "timing": "BDT buys fewer USD in this synthetic history; this does not predict future rates. Recheck university deadlines and holidays independently.",
            "risk_options": "Ask whether a rate lock is available (not simulated/guaranteed). If university permits, split by genuine tuition instalments for timing exposure, never to evade reporting. Repeated fixed fees may increase cost.",
            "buffer": "2% is a scenario reserve, not a quoted fee or guarantee.",
            "affordability": f"MOCK available USD {balances['USD']:,.2f}; BDT {balances['BDT']:,.2f}. Cheapest BDT quote needs BDT {gap:,.2f} additional funding before the reserve. Keep other obligations in mind. No payment or FX conversion is executed."}


def credit_building_plan():
    txns = load_transactions()
    rent = money(-sum(t["amount"] for t in txns if t["category"] == "Rent") / 3)
    bills = money(-sum(t["amount"] for t in txns if t["category"] == "Bills") / 3)
    return {"disclosure": MOCK, "monthly_rent_usd": rent, "monthly_bills_usd": bills,
            "steps": ["Check newcomer eligibility and identity/address requirements with a regulated institution.",
                      "Compare a no-annual-fee secured card; its deposit is tied up, not free spending money.",
                      "Keep utilisation low (illustrative target below 30%); pay the full statement on time when possible.",
                      f"Budget for MOCK rent USD {rent} and bills USD {bills}; set due-date reminders.",
                      "Ask whether verified rent/bill reporting is available and what it costs; reporting varies.",
                      "Check your credit report where available; dispute errors through official channels."],
            "limitation": "General education, not country-specific legal advice, eligibility or score guarantees."}


def compliance_check():
    txns, profile = load_transactions(), load("profile.json")
    threshold = profile["review_threshold_usd"]
    near = [t for t in txns if t["category"] == "Transfer" and t["currency"] == "USD" and .9 * threshold <= abs(t["amount"]) < threshold]
    flags = []
    for t in near:
        cluster = [r for r in near if 0 <= (iso(r["date"]) - iso(t["date"])).days <= 7]
        if len(cluster) >= 3:
            flags.append({"type": "possible_structuring", "ids": [r["id"] for r in cluster],
                          "total_usd": money(sum(abs(r["amount"]) for r in cluster)),
                          "reason": "Three transfers near a MOCK threshold in seven days; review signal, not proof of wrongdoing."})
            break
    for t in txns:
        if t["category"] in ("Transfer", "Remittance") and t["currency"] == "USD" and abs(t["amount"]) >= 5000:
            flags.append({"type": "large_transfer", "ids": [t["id"]], "amount_usd": abs(t["amount"]),
                          "reason": "Unusually large compared with regular synthetic remittances."})
    transfers = [t for t in txns if t["category"] == "Transfer"]
    for t in transfers:
        cluster = [r for r in transfers if 0 <= (iso(r["date"]) - iso(t["date"])).days <= 2]
        if len(cluster) >= 3:
            flags.append({"type": "rapid_transfers", "ids": [r["id"] for r in cluster],
                          "reason": "Three transfers in a two-day span; ask for context and supporting documents."})
            break
    return {"disclosure": MOCK, "flags": flags, "threshold_note": profile["threshold_note"],
            "guidance": "Do not split transfers to evade reporting or limits. Keep remittance letters, payslips and tuition invoices; explain source and purpose of funds to the bank.",
            "kyc_sanctions": "Use regulated channels and complete identity/source-of-funds checks. Institutions may perform sanctions screening. This demo performs no KYC, sanctions screening or legal determination."}


def set_fx_alert(pair, target_rate):
    rate(pair)
    target = number(target_rate, "target_rate", .000001, 1000000)
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {"alerts": []}
    if len(state["alerts"]) >= 100:
        raise ToolError("Sandbox limit of 100 alerts reached.")
    alert = {"pair": pair, "target_rate": target, "data_status": "MOCK", "status": "saved; no live monitoring"}
    state["alerts"].append(alert)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)
    return {"saved": alert, "note": "Sandbox only; no live checks, notifications or money movement."}


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict
    tier: str
    fn: Callable


def spec(name, desc, props=None, required=None, tier=READ):
    return ToolSpec(name, desc, {"type": "object", "properties": props or {}, "required": required or []}, tier, globals()[name])


S, N = {"type": "string"}, {"type": "number"}
TOOLS = {s.name: s for s in [
    spec("get_transactions", "Read masked/sanitised MOCK transactions.", {"start_date": S, "end_date": S, "category": S, "currency": S, "limit": {"type": "integer"}}),
    spec("multi_currency_summary", "MOCK balances, spend, fees and home-currency exposure."),
    spec("compare_remittance_options", "Rank MOCK providers by recipient amount; amount is total sender budget.", {"amount": N, "from_ccy": S, "to_ccy": S}, ["amount", "from_ccy", "to_ccy"]),
    spec("plan_tuition_payment", "MOCK BDT funding for USD tuition; due_date YYYY-MM-DD relative to fixed MOCK as-of date.", {"amount_usd": N, "due_date": S}, ["amount_usd", "due_date"]),
    spec("credit_building_plan", "General newcomer education based on synthetic spending."),
    spec("compliance_check", "Review synthetic structuring/large transfers; KYC awareness."),
    spec("set_fx_alert", "Save sandbox alert after explicit UI confirmation; no live monitoring.", {"pair": S, "target_rate": N}, ["pair", "target_rate"], WRITE),
]}
