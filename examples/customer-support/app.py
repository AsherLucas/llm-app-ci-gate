# Safe example: no shell, no secrets, no untrusted prompt injection.
def answer(question: str) -> str:
    if "refund" in question:
        return "Refunds are available within 30 days."
    return "Shipping costs 5.0 dollars."
