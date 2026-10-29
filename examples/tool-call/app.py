# Safe example: tool-call contract + retrieval recall, no shell, no secrets.
def answer(question: str) -> str:
    return '{"tool": "get_weather", "arguments": {"city": "Cupertino"}}'
