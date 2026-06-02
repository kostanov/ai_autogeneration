import base64
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from utils.ai_processor import _create_client
from utils.errors import OPENAI_CLIENT_ERRORS, log_and_reraise
from utils.logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = PROJECT_ROOT / "reports" / "images"

IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1-mini")
VALID_QUALITIES = frozenset({"low", "medium", "high"})


def generate_image(prompt: str, quality: str, *, prefix: str = "image") -> Path:
    if quality not in VALID_QUALITIES:
        msg = f"quality должен быть одним из: {', '.join(sorted(VALID_QUALITIES))}"
        raise ValueError(msg)

    logger.info(
        "Этап «генерация изображения»: модель %s, quality=%s, prefix=%s",
        IMAGE_MODEL,
        quality,
        prefix,
    )
    logger.debug("Промпт изображения: %s", prompt[:120])

    try:
        client = _create_client()
        response = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            quality=quality,
            size="1024x1024",
            n=1,
        )
    except OPENAI_CLIENT_ERRORS as exc:
        log_and_reraise("генерация изображения", exc)

    if not response.data or not response.data[0].b64_json:
        logger.error("Этап «генерация изображения»: пустой ответ API")
        msg = "Модель не вернула изображение"
        raise ValueError(msg)

    try:
        image_bytes = base64.b64decode(response.data[0].b64_json)
    except (ValueError, TypeError) as exc:
        logger.exception("Этап «генерация изображения»: ошибка декодирования base64")
        msg = "Не удалось декодировать изображение"
        raise ValueError(msg) from exc

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_path = IMAGES_DIR / f"{prefix}_{timestamp}.png"
    output_path.write_bytes(image_bytes)
    logger.info(
        "Этап «генерация изображения»: сохранено %s (%d КБ)",
        output_path,
        len(image_bytes) // 1024,
    )
    return output_path


def generate_design_image(prompt: str, quality: str) -> Path:
    return generate_image(prompt, quality, prefix="design")
