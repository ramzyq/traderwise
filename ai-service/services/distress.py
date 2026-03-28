DISTRESS_TERMS = {
    "mensu adwene",
    "i am overwhelmed",
    "i can't cope",
    "i cant cope",
    "i am in distress",
    "me ho ye den"
}


DISTRESS_REPLY = (
    "Mete wo ase. Wopɛ mmoa mprempren, na yebetumi agye ahotɔ nkakrankakra. "
    "Hena na wobɛtumi afrɛ no seesei de agyina wo akyi?"
)


def detect_distress(message: str) -> bool:
    normalized = message.lower()
    return any(term in normalized for term in DISTRESS_TERMS)
