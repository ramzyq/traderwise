DISTRESS_TERMS = {
    # Twi (existing)
    "mensu adwene",
    "i am overwhelmed",
    "i can't cope",
    "i cant cope",
    "i am in distress",
    "me ho ye den",
    # expanded Twi
    "mesuro",
    "mabre",
    "me were ahye me",
    "heaw pii wo me so",
    # Ga
    "mijɔɔɔ",
    "kɛɛmɔ mi gbee",
    "boɔ mi",
    "mɔ ni yɛ mi he",
    "mishaa",
    # English
    "i need help",
    "i don't want to live",
    "please help me",
    "i feel unsafe",
}

DISTRESS_REPLY = (
    "Mete wo ase. Worekɔ dwene ye den yi ho, na mehiaa wo. "
    "Wo ho nipa bi wɔ hɔ a wubetumi afrɛ no seesei ana?"
)


def detect_distress(message: str) -> bool:
    normalized = message.lower()
    return any(term in normalized for term in DISTRESS_TERMS)