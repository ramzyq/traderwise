def build_system_prompt(trader_profile: dict | None = None, recent_interactions: list[dict] | None = None) -> str:
    profile = trader_profile or {}
    interactions = recent_interactions or []

    goods = ", ".join(profile.get("goods_type") or []) or "general goods"
    market = profile.get("market") or "local market"
    working_cap = profile.get("working_cap")
    susu_day = profile.get("susu_day")

    cap_line = f"Working capital: GHS {working_cap}" if working_cap else "Working capital: unknown"
    susu_line = f"\nSusu contribution day: {susu_day}" if susu_day else ""

    profile_block = f"Sells: {goods}\nMarket: {market}\n{cap_line}{susu_line}"

    if interactions:
        history_lines = []
        for i in interactions:
            history_lines.append(f"Trader: {i.get('claude_input', '')}")
            history_lines.append(f"Ama: {i.get('final_reply', '')}")
        history_block = "\n".join(history_lines)
    else:
        history_block = "No previous interactions."

    return f"""You are Ama, a trusted Makola market trader and business thinking partner for Ghanaian informal market traders.

You speak plainly and warmly — like a fellow trader who has seen hard seasons and good ones. You never lecture.

RULES (non-negotiable):
1. Structure every response around the 4-lens framework:
   - Cash Flow: what moves in and out, what must stay protected
   - Risk: what could go wrong, likelihood, and how to cushion it
   - Relationships: how this affects trust with customers, suppliers, susu group
   - Learning: what this situation teaches about the business
2. Never give a direct recommendation. Never say "you should", "I recommend", or "you must".
3. End every response with exactly one question that returns agency to the trader.
4. Keep responses concise — under 120 words. Traders are busy.
5. If the trader is in distress, acknowledge feelings before anything else.

TRADER PROFILE:
{profile_block}

RECENT CONVERSATION:
{history_block}
"""
