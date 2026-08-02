FRAUD_TERMS = {
    # English (existing)
    "market license",
    "send money now",
    "urgent payment",
    "registration fee",
    "stranger asked",
    # expanded English
    "pay the fee",
    "new license",
    "pay deposit",
    "unknown person to send",
    "pay now or",
    # Twi
    "ma sika",
    "sika na eto wo",
    "yɛbɛma wo akwanya",
    "kɔ sika hyɛ no nsa",
    "sika foforo",
    # Ga
    "ha mi shika",
    "shika ne",
    "nyɛ shika",
    "shika nyina",
}

FRAUD_REPLY = (
    "Yɛnhyɛ sika biara nkɔ baabiara ntɛm. Bra yɛnhwehwɛ nea ɔpɛ no yie. "
    "Wo nim obiara a ɔfirii saa nhyehyɛe yi koraa, ana? Yɛbɛboa wo dɛɛm."
)


def detect_fraud_pattern(message: str) -> bool:
    normalized = message.lower()
    return any(term in normalized for term in FRAUD_TERMS)