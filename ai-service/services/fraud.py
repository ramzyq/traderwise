FRAUD_TERMS = {
    "market license",
    "send money now",
    "urgent payment",
    "registration fee",
    "stranger asked"
}


FRAUD_REPLY = (
    "Yɛnhyɛ sika biara nkɔ baabiara ntɛm. Bra yɛnhwehwɛ nea ɔpɛ no yie. "
    "Wo nim nipa no anaa woatumi ahwɛ ne nkrataa anaa?"
)


def detect_fraud_pattern(message: str) -> bool:
    normalized = message.lower()
    return any(term in normalized for term in FRAUD_TERMS)
