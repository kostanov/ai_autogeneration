import json

from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError

from utils.logging_config import get_logger

logger = get_logger(__name__)


def api_error_hint(exc: APIError) -> str:
    body = getattr(exc, "body", None) or {}
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return ""
    code = (body.get("error") or {}).get("code", "")
    if code == "unsupported_country_region_territory":
        return (
            " Укажите OPENAI_BASE_URL в .env (прокси-провайдер) "
            "или запустите с --mock."
        )
    return ""


def format_api_error(exc: APIError) -> str:
    return f"Ошибка API OpenAI: {exc}{api_error_hint(exc)}"


def log_and_reraise(stage: str, exc: BaseException) -> None:
    logger.exception("Ошибка на этапе «%s»: %s", stage, exc)
    raise exc


OPENAI_CLIENT_ERRORS = (
    APIError,
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
)
