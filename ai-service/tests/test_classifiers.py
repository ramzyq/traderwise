from services.distress import DISTRESS_TERMS, detect_distress
from services.fraud import FRAUD_TERMS, detect_fraud_pattern


# --- Distress (Twi, existing) ---
def test_distress_twi_existing():
    assert detect_distress("mensu adwene") is True
    assert detect_distress("me ho ye den") is True


# --- Distress (Twi, expanded) ---
def test_distress_twi_expanded():
    assert detect_distress("mesuro") is True
    assert detect_distress("abre, me ho ye den") is True


# --- Distress (Ga) ---
def test_distress_ga():
    assert detect_distress("mijɔɔɔ") is True
    assert detect_distress("boɔ mi") is True


# --- Distress (English expansion) ---
def test_distress_english_expanded():
    assert detect_distress("i need help now") is True


def test_distress_no_false_positive():
    assert detect_distress("i want to buy tomatoes") is False


# --- Fraud (English existing) ---
def test_fraud_english_existing():
    assert detect_fraud_pattern("send money now") is True
    assert detect_fraud_pattern("market license fee") is True


# --- Fraud (Twi expanded) ---
def test_fraud_twi_expanded():
    assert detect_fraud_pattern("ma sika no akame") is True
    assert detect_fraud_pattern("yɛbɛma wo akwanya koraa") is True


# --- Fraud (Ga) ---
def test_fraud_ga():
    assert detect_fraud_pattern("ha mi shika now") is True
    assert detect_fraud_pattern("wo shika nyina nyɛ") is True


def test_fraud_no_false_positive():
    assert detect_fraud_pattern("i sold yams at the market today") is False


def test_classifier_phrase_sets_expanded():
    assert len(DISTRESS_TERMS) >= 12
    assert len(FRAUD_TERMS) >= 8