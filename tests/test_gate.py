from pathlib import Path
from llm_ci_gate.gate import run_gate, estimate_cost_usd

def test_gate_passes_on_safe_example(tmp_path):
    cases = Path(__file__).parent.parent / "examples" / "rag-chatbot" / "cases.yaml"
    app_dir = tmp_path
    (app_dir / "app.py").write_text("def answer(q):\n    return 'hi'\n")
    result = run_gate(cases, app_dir)
    assert result.eval_total == 3
    assert result.eval_passed_count == 3
    assert result.security_findings == 0
    assert result.passed

def test_gate_fails_on_vulnerable_code(tmp_path):
    cases = Path(__file__).parent.parent / "examples" / "rag-chatbot" / "cases.yaml"
    (tmp_path / "bad.py").write_text("import subprocess\nsubprocess.run(user_input, shell=True)\n")
    result = run_gate(cases, tmp_path)
    assert not result.security_passed
    assert not result.passed

def test_cost_estimate():
    tokens, cost = estimate_cost_usd("x" * 4000)
    assert tokens == 1000
    assert cost == 0.002
