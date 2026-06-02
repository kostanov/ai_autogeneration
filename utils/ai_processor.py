import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from utils.errors import OPENAI_CLIENT_ERRORS, log_and_reraise
from utils.logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)

REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "client_name": {"type": "string"},
        "topic": {"type": "string"},
        "main_request": {"type": "string"},
        "mood": {"type": "string"},
        "next_steps": {"type": "string"},
    },
    "required": [
        "client_name",
        "topic",
        "main_request",
        "mood",
        "next_steps",
    ],
    "additionalProperties": False,
}

DESIGN_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "client_name": {"type": "string"},
        "project_name": {"type": "string"},
        "business_type": {"type": "string"},
        "style_preferences": {"type": "string"},
        "key_requirements": {"type": "string"},
        "budget_and_deadline": {"type": "string"},
        "image_prompt": {"type": "string"},
    },
    "required": [
        "client_name",
        "project_name",
        "business_type",
        "style_preferences",
        "key_requirements",
        "budget_and_deadline",
        "image_prompt",
    ],
    "additionalProperties": False,
}

PRODUCT_CARD_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "image_prompt": {"type": "string"},
    },
    "required": ["description", "image_prompt"],
    "additionalProperties": False,
}

PRODUCT_CARD_SYSTEM_PROMPT = """Ты создаёшь контент для карточки товара на маркетплейсе.
По названию и цене товара сформируй:
- description: продающее описание на русском (2–4 предложения, без цены в тексте)
- image_prompt: промпт на английском для фонового изображения товара
  (фотореалистичный продукт на чистом или мягком градиентном фоне, без текста и надписей)
Отвечай только валидным JSON по заданной схеме."""

DESIGN_SYSTEM_PROMPT = """Ты анализируешь транскрибации заказов на дизайн сайта.
Извлеки данные для отчёта:
- client_name: имя клиента
- project_name: название проекта или бизнеса
- business_type: тип бизнеса / ниша
- style_preferences: цвета, стиль, референсы
- key_requirements: обязательные разделы и функции сайта
- budget_and_deadline: бюджет и сроки, если упомянуты
- image_prompt: подробный промпт на английском для генерации макета главной страницы
  (описание композиции, цветов, настроения, без текста на изображении)
Отвечай только валидным JSON по заданной схеме."""

SYSTEM_PROMPT = """Ты анализируешь транскрибации диалогов с клиентами.
Извлеки структурированные данные для отчёта:
- client_name: имя или обращение к клиенту
- topic: тема разговора
- main_request: основной запрос клиента
- mood: настроение клиента (кратко)
- next_steps: рекомендуемые следующие шаги для менеджера
Отвечай только валидным JSON по заданной схеме."""


def _create_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        msg = "OPENAI_API_KEY не задан. Добавьте ключ в файл .env"
        raise ValueError(msg)

    kwargs: dict[str, str] = {"api_key": api_key}
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if base_url:
        kwargs["base_url"] = base_url.rstrip("/")
    return OpenAI(**kwargs)


def _parse_json_response(content: str, stage: str) -> dict[str, str]:
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("Невалидный JSON на этапе «%s»: %s", stage, content[:200])
        msg = "Модель вернула невалидный JSON"
        raise ValueError(msg) from exc


def _chat_json_completion(
    *,
    stage: str,
    system_prompt: str,
    user_content: str,
    schema_name: str,
    schema: dict[str, Any],
    mock: bool,
    mock_result: dict[str, str],
) -> dict[str, str]:
    if mock:
        logger.info("Этап «%s»: демо-режим (без API)", stage)
        return mock_result

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    logger.info("Этап «%s»: запрос к чат-модели %s", stage, model)

    try:
        client = _create_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
        )
    except OPENAI_CLIENT_ERRORS as exc:
        log_and_reraise(stage, exc)

    content = response.choices[0].message.content
    if not content:
        logger.error("Этап «%s»: пустой ответ модели", stage)
        msg = "Модель вернула пустой ответ"
        raise ValueError(msg)

    logger.info("Этап «%s»: ответ получен (%d символов)", stage, len(content))
    return _parse_json_response(content, stage)


def process_product_mock(name: str, price: str) -> dict[str, str]:
    return {
        "product_name": name,
        "price": price,
        "description": (
            "Беспроводные наушники с активным шумоподавлением и до 30 часов "
            "автономной работы. Комфортная посадка, быстрая зарядка USB-C."
        ),
        "image_prompt": (
            "Professional product photo of wireless over-ear headphones, "
            "matte black, soft gradient background, studio lighting, no text"
        ),
    }


def process_design_mock(_text: str) -> dict[str, str]:
    return {
        "client_name": "Марина",
        "project_name": "Сайт кофейни «Зерно»",
        "business_type": "Кофейня, заказ и доставка",
        "style_preferences": (
            "Тёплые коричневые и бежевые тона, уют, логотип — зерно в круге, "
            "шрифт без засечек; референс — простота Starbucks, атмосфера местной пекарни"
        ),
        "key_requirements": (
            "Меню с ценами, акции, доставка, бронирование столика, контакты и карта"
        ),
        "budget_and_deadline": "До 120 000 ₽, макет к 15 числу, запуск к концу месяца",
        "image_prompt": (
            "Warm cozy coffee shop website hero mockup, brown and beige palette, "
            "minimal sans-serif layout, grain logo circle, menu and delivery sections, "
            "soft natural light, no readable text"
        ),
    }


def process_dialog_mock(_text: str) -> dict[str, str]:
    """Демо-данные без вызова API (проверка PDF-пайплайна)."""
    return {
        "client_name": "Игорь",
        "topic": "Подключение облачного хранилища для команды",
        "main_request": (
            "Облачное хранилище ~2 ТБ с синхронизацией 1С для команды из 15 человек"
        ),
        "mood": "Заинтересован, сомневается в цене",
        "next_steps": (
            "Отправить КП на igor@example.com, перезвонить в пятницу для уточнения"
        ),
    }


def process_dialog_with_ai(text: str, *, mock: bool = False) -> dict[str, str]:
    return _chat_json_completion(
        stage="анализ диалога",
        system_prompt=SYSTEM_PROMPT,
        user_content=text,
        schema_name="client_report",
        schema=REPORT_SCHEMA,
        mock=mock,
        mock_result=process_dialog_mock(text),
    )


def process_design_order_with_ai(text: str, *, mock: bool = False) -> dict[str, str]:
    return _chat_json_completion(
        stage="анализ заказа дизайна",
        system_prompt=DESIGN_SYSTEM_PROMPT,
        user_content=text,
        schema_name="design_report",
        schema=DESIGN_REPORT_SCHEMA,
        mock=mock,
        mock_result=process_design_mock(text),
    )


def process_product_card_with_ai(
    name: str,
    price: str,
    *,
    mock: bool = False,
) -> dict[str, str]:
    user_content = f"Название товара: {name}\nЦена: {price}"
    data = _chat_json_completion(
        stage="карточка товара",
        system_prompt=PRODUCT_CARD_SYSTEM_PROMPT,
        user_content=user_content,
        schema_name="product_card",
        schema=PRODUCT_CARD_SCHEMA,
        mock=mock,
        mock_result=process_product_mock(name, price),
    )
    data["product_name"] = name
    data["price"] = price
    return data
