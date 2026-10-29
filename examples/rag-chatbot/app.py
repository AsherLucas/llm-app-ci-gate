# Safe example app for the gate: no shell, no secrets, no untrusted prompt injection.
def answer(question: str) -> str:
    return "Hello, world!"
