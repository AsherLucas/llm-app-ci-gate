# llm-app-ci-gate

One CI gate for LLM apps: prompt evaluation + security scan + cost estimate, in a single report.

It does not reimplement scoring or scanning. It runs two published tools you can also use separately:

- [prompt-eval-harness](https://github.com/AsherLucas/prompt-eval-harness) — deterministic prompt evaluation (exact, regex, JSON Schema, citation, forbidden, numeric_close, …)
- [llm-app-security-scanner](https://github.com/AsherLucas/llm-app-security-scanner) — static security scan for LLM/agent repos (shell, secrets, untrusted input, JS/TS eval, …)

Plus an offline cost estimate (~4 chars per token, no model call, no network).

## Quickstart

```bash
pip install llm-app-ci-gate
llm-ci-gate check --cases examples/rag-chatbot/cases.yaml --path examples/rag-chatbot
```

Exit 0 = PASS, exit 1 = FAIL. It writes `llm-ci-gate-report.md` and `llm-ci-gate-report.json`.

## GitHub Action

```yaml
- uses: AsherLucas/llm-app-ci-gate@v0.1.0
  with:
    cases: cases.yaml
    path: .
```

## Why one gate?

LLM apps fail in three different ways at once: a prompt regresses, a tool call leaks a secret, and a prompt change doubles cost. Running three separate checks in CI is easy to skip one of. One gate, one report, one pass/fail makes it hard to forget.
