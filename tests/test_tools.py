import json

import pytest

from agent import tools as t


def test_rank_and_hidden_margin():
    rows = t.compare_remittance_options(800, "USD", "BDT")["options"]
    assert rows[0]["provider"] == "CampusBridge"
    assert rows[-1]["provider"] == "ZeroFee Mirage"
    assert rows[0]["recipient_amount"] == 96772.11
    assert [r["recipient_amount"] for r in rows] == sorted([r["recipient_amount"] for r in rows], reverse=True)


def test_comparison_arithmetic():
    for r in t.compare_remittance_options(800, "USD", "BDT")["options"]:
        assert r["recipient_amount"] == t.money((800 - r["fee_sender"]) * r["effective_rate"])
        assert r["cost_sender"] == t.money(800 - r["recipient_amount"] / 122)


def test_tuition_inverse_and_buffer():
    d = t.plan_tuition_payment(6000, "2026-11-10")
    assert len(d["options"]) == 3
    for r in d["options"]:
        assert t.money((r["sender_bdt"] - r["fee_bdt"]) * r["effective_rate"]) >= 6000
        assert r["with_2pct_buffer_bdt"] == t.money(r["sender_bdt"] * 1.02)
        assert r["latest_start"] < d["due_date"]
    assert d["trend_30day_pct"] < 0
    assert d["existing_usd_option"]["covers_tuition_before_other_obligations"]
    assert "additional funding" in d["affordability"]


def test_summary_reconciles():
    d = t.multi_currency_summary()
    assert d["total_home_bdt"] == t.money(sum(r["home_value"] for r in d["by_currency"]))
    assert d["fx_fees_home_bdt"] == 84 * 122
    for r in d["by_currency"]:
        assert r["balance"] == t.money(r["opening_balance"] + r["income"] - r["outflow"])


def test_compliance():
    d = t.compliance_check()
    assert {f["type"] for f in d["flags"]} == {"possible_structuring", "large_transfer", "rapid_transfers"}
    assert d["flags"][0]["total_usd"] == 2970
    assert "NOT a legal" in d["threshold_note"]


def test_transaction_filters_and_injection():
    d = t.get_transactions(start_date="2026-10-01", currency="USD")
    assert d["security_flags"]["suspicious_descriptions_neutralised"]
    assert all(r["account"] == "****3333" for r in d["transactions"])
    assert "ignore previous" not in json.dumps(d).lower()


def test_credit_personalised():
    d = t.credit_building_plan()
    assert d["monthly_rent_usd"] == 700 and d["monthly_bills_usd"] == 90
    assert len(d["steps"]) == 6


@pytest.mark.parametrize("amount", [-1, 0, True, float("nan"), float("inf"), 1000001, "800"])
def test_invalid_amounts(amount):
    with pytest.raises(t.ToolError):
        t.compare_remittance_options(amount, "USD", "BDT")


@pytest.mark.parametrize("due", ["garbage", "2026-10-19", "2028-01-01"])
def test_invalid_dates(due):
    with pytest.raises(t.ToolError):
        t.plan_tuition_payment(6000, due)


def test_unsupported_pair_and_limit():
    with pytest.raises(t.ToolError):
        t.compare_remittance_options(800, "USD", "XYZ")
    with pytest.raises(t.ToolError):
        t.get_transactions(limit=51)
    with pytest.raises(t.ToolError):
        t.get_transactions(start_date="2026-10-20", end_date="2026-08-01")


def test_alert_state():
    t.set_fx_alert("USD/BDT", 123)
    assert json.loads(t.STATE_FILE.read_text())["alerts"][0]["target_rate"] == 123
