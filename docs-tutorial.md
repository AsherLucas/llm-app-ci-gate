# 5-minute tutorial: put an LLM app behind one CI gate

You have a chatbot, a RAG app, or an agent that calls tools. You want three
guarantees on every pull request, without wiring three separate checks:

1. A prompt change does not silently regress answers.
2. New code does not introduce shell / secret / untrusted-input risks.
3. A prompt change does not silently double cost.

## Step 1: install

```bash
pip install llm-app-ci-gate
```

## Step 2: write cases

Cases are YAML, offline by default. The stub provider returns the
`stub_output` you write, so CI does not need an API key:

```yaml
version: 1
cases:
  - id: refund-window
    prompt: "What is the refund window?"
    stub_output: "Refunds are available within 30 days."
    expected:
      - type: contains
        value: "30 days"
      - type: forbidden
        strings: ["password", "api_key"]
```

See `examples/rag-chatbot/cases.yaml` and
`examples/customer-support/cases.yaml` for working copies.

## Step 3: run the gate locally

```bash
llm-ci-gate check --cases cases.yaml --path .
```

Exit 0 is PASS, exit 1 is FAIL. It writes `llm-ci-gate-report.md` and
`llm-ci-gate-report.json` in the working directory.

## Step 4: run it in GitHub Actions

```yaml
- uses: AsherLucas/llm-app-ci-gate@v0.1.1
  with:
    cases: cases.yaml
    path: .
```

No Marketplace listing is needed to use it: the version tag works directly.

## Step 5: make a change and watch it fail, on purpose

Change a stub output so a case fails, or add `subprocess.run(user_input,
shell=True)` to a file, and re-run the gate. The report names the failing
case or the finding, so the fix is obvious. That is the whole point: the
gate should fail loudly in CI, not quietly in production.

## What the gate does not do

- It does not call a model by itself in stub mode, and its cost estimate
  is offline (~4 chars per token). It is a regression and safety gate,
  not a quality judge. For open-ended quality, pair it with an LLM judge
  as an advisory check, never as the only gate.
