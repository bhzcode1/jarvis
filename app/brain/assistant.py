from openai import OpenAI

from config.settings import Settings
from app.memory.store import format_memory_context
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_ai_response(user_text: str, settings: Settings) -> str:
    """Generate assistant response using OpenAI chat completions."""
    if not settings.openai_api_key:
        return "OpenAI API key is missing. Please set OPENAI_API_KEY in your .env file."

    if not user_text.strip():
        return "Please say that again. I did not catch your request."

    client = OpenAI(api_key=settings.openai_api_key)
    memory_context = format_memory_context() if settings.memory_enabled else "Memory disabled."
    system_prompt = (
        f"You are {settings.assistant_name}, a concise, helpful desktop AI assistant.\n"
        f"Use the following persistent user memory when useful:\n{memory_context}"
    )

    try:
        response = client.chat.completions.create(
            model=settings.default_model,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        )
    except Exception as error:  # pragma: no cover - network/API runtime guard
        logger.exception("OpenAI request failed: %s", error)
        return "I could not reach the AI service right now. Please try again."

    message = response.choices[0].message.content or ""
    return message.strip() or "I am sorry, I could not generate a response."
