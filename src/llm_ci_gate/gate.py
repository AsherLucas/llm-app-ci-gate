"""Orchestrate prompt-eval and llm-scan into one gate report.

This module does not reimplement scoring or scanning: it runs the two
published tools (prompt-eval-harness and llm-app-security-scanner) and
combines their results, plus a simple offline cost estimate, into one
machine-readable report. That keeps the gate's behaviour identical to
running the two tools separately, while giving CI a single pass/fail.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GateResult:
    eval_passed: bool
    eval_total: int
    eval_passed_count: int
    security_passed: bool
    security_findings: int
    security_high: int
    estimated_tokens: int
    estimated_cost_usd: float
    passed: bool = False
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "eval": {"passed": self.eval_passed, "total": self.eval_total, "passed_count": self.eval_passed_count},
            "security": {"passed": self.security_passed, "findings": self.security_findings, "high": self.security_high},
            "cost_estimate": {"estimated_tokens": self.estimated_tokens, "estimated_cost_usd": round(self.estimated_cost_usd, 6)},
            "details": self.details,
        }


def estimate_cost_usd(text: str, price_per_1k: float = 0.002) -> tuple[int, float]:
    """Offline estimate: ~4 chars per token, no model call, no network."""
    tokens = max(1, len(text) // 4) if text else 0
    return tokens, tokens / 1000 * price_per_1k


def run_gate(cases: Path, path: Path, threshold: float = 1.0, fail_on: str = "high") -> GateResult:
    """Run prompt-eval (stub provider, offline) and llm-scan, combine."""
    # Eval: use the prompt_eval Python API if available, else CLI fallback.
    eval_total = eval_passed_count = 0
    eval_passed = False
    eval_detail = ""
    try:
        from prompt_eval.runner import run_cases  # type: ignore
        from prompt_eval.cli import load_cases  # type: ignore
        from prompt_eval.providers import StubProvider  # type: ignore
    except Exception as exc:  # pragma: no cover - fallback path
        eval_detail = f"prompt_eval import failed: {exc}"
        run_cases = None  # type: ignore
        load_cases = None  # type: ignore
    if run_cases is not None:
        try:
            case_list = load_cases(Path(cases))
            eval_total = len(case_list)
            report = run_cases(case_list, provider=StubProvider())
            results = report.results if hasattr(report, "results") else report
            eval_passed_count = sum(1 for r in results if getattr(r, "passed", False))
            eval_passed = eval_total > 0 and eval_passed_count / eval_total >= threshold
        except Exception as exc:
            eval_detail = f"eval run failed: {exc}"
    if eval_total == 0 and not eval_detail:
        # CLI fallback: run prompt-eval run and parse its JSON if produced.
        out = Path("llm-ci-gate-eval.json")
        proc = subprocess.run([sys.executable, "-m", "prompt_eval", "run", "--cases", str(cases), "--provider", "stub", "--json", str(out)], capture_output=True, text=True)
        eval_detail = proc.stdout[-500:] + proc.stderr[-500:]
        if out.exists():
            try:
                data = json.loads(out.read_text())
                eval_total = int(data.get("total", 0))
                eval_passed_count = int(data.get("passed", 0))
                eval_passed = eval_total > 0 and eval_passed_count / eval_total >= threshold
            except Exception:
                pass

    # Security: use llm_scanner API.
    sec_findings = sec_high = 0
    sec_passed = True
    try:
        from llm_scanner.scanner import scan_path
        result = scan_path(path)
        sec_findings = len(result.findings)
        sec_high = sum(1 for f in result.findings if f.severity == "high")
        # Gate mirrors llm-scan --fail-on: high fails by default.
        sec_passed = not (fail_on == "high" and sec_high > 0)
    except Exception as exc:
        sec_passed = False
        eval_detail += f" security scan failed: {exc}"

    # Cost: estimate from cases file text (offline, no API).
    text = cases.read_text(encoding="utf-8", errors="ignore") if cases.exists() else ""
    tokens, cost = estimate_cost_usd(text)
    passed = eval_passed and sec_passed
    return GateResult(
        eval_passed=eval_passed, eval_total=eval_total, eval_passed_count=eval_passed_count,
        security_passed=sec_passed, security_findings=sec_findings, security_high=sec_high,
        estimated_tokens=tokens, estimated_cost_usd=cost, passed=passed,
        details={"eval_detail": eval_detail, "threshold": threshold, "fail_on": fail_on},
    )
