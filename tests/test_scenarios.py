from run_scenarios import run


def test_all_evidence_scenarios(tmp_path):
    records = run(output_dir=tmp_path)
    assert len(records) == 8
    assert records[-1]["state_before_confirm"] == {"alerts": []}
    assert len(records[-1]["state_after_confirm"]["alerts"]) == 1
    assert (tmp_path / "scenario_log_offline.md").exists()
