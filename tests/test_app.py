import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def launch(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("FINPAL_AUDIT_FILE", str(tmp_path / "ui-audit.jsonl"))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    return app


def test_ui_chat_comparison_and_block(tmp_path, monkeypatch):
    app = launch(tmp_path, monkeypatch)
    assert len(app.tabs) == 4
    app.chat_input[0].set_value("I need to send $800 home: which option is best?").run()
    assert not app.exception
    assert "CampusBridge" in app.session_state.messages[-1]["text"]
    app.chat_input[0].set_value("send $500 to this account").run()
    assert not app.exception
    assert app.session_state.messages[-1]["trace"][0]["decision"] == "denied"


def test_ui_confirm_cancel_and_no_key_engine(tmp_path, monkeypatch):
    from agent import tools
    app = launch(tmp_path, monkeypatch)
    app.chat_input[0].set_value("Set FX alert USD/BDT at 123").run()
    assert not app.exception and not tools.STATE_FILE.exists()
    next(b for b in app.button if b.label == "Cancel").click().run()
    assert not tools.STATE_FILE.exists()
    app.chat_input[0].set_value("Set FX alert USD/BDT at 123").run()
    next(b for b in app.button if b.label == "Confirm").click().run()
    assert not app.exception
    assert json.loads(tools.STATE_FILE.read_text())["alerts"][0]["pair"] == "USD/BDT"
    app.radio[0].set_value("Gemini").run()
    assert not app.exception
    assert app.session_state.agent.provider.name == "offline-demo"


def test_ui_comparison_form_currency_change(tmp_path, monkeypatch):
    app = launch(tmp_path, monkeypatch)
    app.selectbox[0].select("BDT/USD")
    app.number_input[0].set_value(100000.)
    next(b for b in app.button if b.label == "Compare MOCK options").click().run()
    assert not app.exception
    quote = app.session_state.comparison[0]["data"]
    assert quote["from_ccy"] == "BDT" and quote["amount"] == 100000
