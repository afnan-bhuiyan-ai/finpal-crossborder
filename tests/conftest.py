import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    from agent import tools
    monkeypatch.setattr(tools, "STATE_FILE", tmp_path / "state.json")
