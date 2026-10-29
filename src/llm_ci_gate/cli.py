"""CLI: llm-ci-gate check --cases cases.yaml --path . [--threshold 1.0] [--fail-on high]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .gate import run_gate


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="llm-ci-gate")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="Run eval + security gate")
    c.add_argument("--cases", default="cases.yaml")
    c.add_argument("--path", default=".")
    c.add_argument("--threshold", type=float, default=1.0)
    c.add_argument("--fail-on", default="high")
    c.add_argument("--markdown", default="llm-ci-gate-report.md")
    c.add_argument("--json", default="llm-ci-gate-report.json")
    args = p.parse_args(argv)
    result = run_gate(Path(args.cases), Path(args.path), threshold=args.threshold, fail_on=args.fail_on)
    Path(args.json).write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    md = (
        f"# LLM App CI Gate\n\n"
        f"**Result: {'PASS' if result.passed else 'FAIL'}**\n\n"
        f"- Eval: {result.eval_passed_count}/{result.eval_total} passed (threshold {args.threshold}) — {'PASS' if result.eval_passed else 'FAIL'}\n"
        f"- Security: {result.security_findings} findings, {result.security_high} high (fail-on {args.fail_on}) — {'PASS' if result.security_passed else 'FAIL'}\n"
        f"- Cost estimate (offline): ~{result.estimated_tokens} tokens, ~${result.estimated_cost_usd:.6f}\n"
    )
    Path(args.markdown).write_text(md, encoding="utf-8")
    print(md)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
