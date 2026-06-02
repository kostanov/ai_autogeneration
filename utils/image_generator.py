import base64
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from utils.ai_processor import _create_client

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = PROJECT_ROOT / "reports" / "images"

IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1-mini")
VALID_QUALITIES = frozenset({"low", "medium", "high"})


def generate_design_image(prompt: str, quality: str) -> Path:
    if quality not in VALID_QUALITIES:
        msg = f"quality должен быть одним из: {', '.join(sorted(VALID_QUALITIES))}"
        raise ValueError(msg)

    client = _create_client()
    response = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        quality=quality,
        size="1024x1024",
        n=1,
    )

    if not response.data or not response.data[0].b64_json:
        msg = "Модель не вернула изображение"
        raise ValueError(msg)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_path = IMAGES_DIR / f"design_{timestamp}.png"
    output_path.write_bytes(base64.b64decode(response.data[0].b64_json))
    return output_path
