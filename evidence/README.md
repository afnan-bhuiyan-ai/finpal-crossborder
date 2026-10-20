# Evidence index

All financial examples are MOCK, and all packaged execution evidence is offline. No key or live Gemini response is included.

| File | Meaning |
|---|---|
| scenario_log_offline.md | Human-readable S1-S8 prompts, replies, policy traces, assertions and compliance supplement |
| results_offline.json | Full numeric tool results, actual provider name, traces, and S8 before/after state |
| audit_offline.jsonl | UTC masked audit events for the scenario session |
| sandbox_offline.json | One confirmed MOCK alert; separate from the interactive app state |
| pytest_final.txt | Actual final pytest output including headless AppTest cases |
| pytest_results.xml | JUnit results with per-test names/timing, including tests/test_app.py |
| BUILD_LOG.md | Incremental build checkpoints and what each verified |

Scenario S8 programmatically simulates the user's confirmation and is labeled as such. AppTest separately clicks **Cancel** and **Confirm** on the real Streamlit application tree, proving that the UI path performs the expected state transition. AppTest is headless UI testing, not a screenshot or a video.

`test_gemini_raw_signature_replay_without_network` builds real SDK response objects, parses a native function call, preserves the original Content object and its synthetic signature, and checks function response ordering. It does not verify live alias availability, account quotas, network access or Gemini task completion.

To regenerate: `python run_scenarios.py --engine offline`. For a free-tier live rerun use `python run_scenarios.py --engine gemini --output-dir evidence/gemini-rerun` after configuring the non-billed project. Inspect actual `provider` and fallback notices; a requested Gemini run that falls back must not be represented as all-Gemini evidence. This runner overwrites only its fixed evidence files in the chosen output directory.
