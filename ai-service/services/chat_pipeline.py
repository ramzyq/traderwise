from prompts.system_prompt import build_system_prompt
from services.claude_client import ClaudeClient
from services.db import get_recent_interactions, get_trader_profile, save_interaction
from services.distress import DISTRESS_REPLY, detect_distress
from services.fraud import FRAUD_REPLY, detect_fraud_pattern
from services.translate import to_english, to_twi
from services.validator import has_hard_violation, post_process_response

TWI_LANGUAGE_CODE = "tw"


class ChatPipeline:
    def __init__(self) -> None:
        self.claude = ClaudeClient()

    def run(self, message: str, phone: str) -> dict:
        distress_flag = detect_distress(message)
        if distress_flag:
            save_interaction(
                phone=phone,
                transcription=None,
                claude_input=message,
                claude_output="",
                final_reply=DISTRESS_REPLY,
                distress_flag=True,
            )
            return {"reply": DISTRESS_REPLY, "distress_flag": True, "fraud_flag": False}

        fraud_flag = detect_fraud_pattern(message)
        if fraud_flag:
            save_interaction(
                phone=phone,
                transcription=None,
                claude_input=message,
                claude_output="",
                final_reply=FRAUD_REPLY,
                fraud_flag=True,
            )
            return {"reply": FRAUD_REPLY, "distress_flag": False, "fraud_flag": True}

        trader_profile = get_trader_profile(phone)
        recent_interactions = get_recent_interactions(phone)

        # Translate message to English for Claude if trader speaks Twi.
        trader_language = trader_profile.get("language", "twi")
        is_twi = trader_language.lower() in ("twi", "tw", "akan")

        english_message = to_english(message, source_language="tw") if is_twi else message

        system_prompt = build_system_prompt(trader_profile, recent_interactions)
        raw_response = self.claude.generate(system_prompt=system_prompt, user_message=english_message)
        validated = post_process_response(raw_response)

        if has_hard_violation(validated):
            # Re-call only on hard violations to reduce latency.
            raw_response = self.claude.generate(system_prompt=system_prompt, user_message=english_message)
            validated = post_process_response(raw_response)

        # Translate reply back to Twi if needed.
        final_reply = to_twi(validated) if is_twi else validated

        save_interaction(
            phone=phone,
            transcription=None,
            claude_input=english_message,
            claude_output=raw_response,
            final_reply=final_reply,
        )

        return {"reply": final_reply, "distress_flag": False, "fraud_flag": False}
