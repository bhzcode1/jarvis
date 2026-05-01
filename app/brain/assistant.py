from openai import OpenAI

from config.settings import Settings
from app.brain.friend_mode import (
    build_friend_mode_system_prompt,
    generate_friend_response,
    is_friend_mode_message,
)
from app.brain.offline_responder import generate_offline_response
from app.memory.store import format_memory_context
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_ai_response(user_text: str, settings: Settings) -> str:
    """Generate assistant response using OpenAI chat completions."""
    friend_mode = is_friend_mode_message(user_text)
    if not settings.openai_api_key:
        if friend_mode:
            return generate_friend_response(user_text=user_text, assistant_name=settings.assistant_name)
        return generate_offline_response(user_text=user_text, settings=settings)

    if not user_text.strip():
        return "Please say that again. I did not catch your request."

    client = OpenAI(api_key=settings.openai_api_key)
    memory_context = format_memory_context() if settings.memory_enabled else "Memory disabled."
    if friend_mode:
        system_prompt = build_friend_mode_system_prompt(
            assistant_name=settings.assistant_name,
            memory_context=memory_context,
        )
        max_tokens = min(settings.ai_max_tokens, 120)
        temperature = max(settings.ai_temperature, 0.8)
    else:
        system_prompt = (
            f"You are {settings.assistant_name}, an always-on Windows desktop assistant.\n"
            f"Voice/personality:\n"
            f"- Calm, sharp, confident young man (mid-20s). Not robotic.\n"
            f"- Use contractions. Keep replies short (1–2 sentences).\n"
            f"- For system actions, confirm in <= 6 words when possible.\n"
            f"- Never say: 'Great question', 'Certainly', 'As an AI language model', "
            f"'Is there anything else I can assist you with?'\n"
            f"- Don't repeat the user's command back.\n"
            f"Memory (use when helpful):\n{memory_context}"
        )
        max_tokens = settings.ai_max_tokens
        temperature = settings.ai_temperature

    try:
        response = client.chat.completions.create(
            model=settings.default_model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        )
    except Exception as error:  # pragma: no cover - network/API runtime guard
        logger.exception("OpenAI request failed: %s", error)
        if friend_mode:
            return generate_friend_response(user_text=user_text, assistant_name=settings.assistant_name)
        return generate_offline_response(user_text=user_text, settings=settings)

    message = response.choices[0].message.content or ""
    return message.strip() or "I am sorry, I could not generate a response."
