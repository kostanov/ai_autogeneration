import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

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
    if mock:
        return process_dialog_mock(text)

    client = _create_client()
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "client_report",
                "strict": True,
                "schema": REPORT_SCHEMA,
            },
        },
    )

    content = response.choices[0].message.content
    if not content:
        msg = "Модель вернула пустой ответ"
        raise ValueError(msg)

    return json.loads(content)


def process_design_order_with_ai(text: str, *, mock: bool = False) -> dict[str, str]:
    if mock:
        return process_design_mock(text)

    client = _create_client()
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": DESIGN_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "design_report",
                "strict": True,
                "schema": DESIGN_REPORT_SCHEMA,
            },
        },
    )

    content = response.choices[0].message.content
    if not content:
        msg = "Модель вернула пустой ответ"
        raise ValueError(msg)

    return json.loads(content)


def process_product_card_with_ai(
    name: str,
    price: str,
    *,
    mock: bool = False,
) -> dict[str, str]:
    if mock:
        return process_product_mock(name, price)

    client = _create_client()
    user_content = f"Название товара: {name}\nЦена: {price}"
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": PRODUCT_CARD_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "product_card",
                "strict": True,
                "schema": PRODUCT_CARD_SCHEMA,
            },
        },
    )

    content = response.choices[0].message.content
    if not content:
        msg = "Модель вернула пустой ответ"
        raise ValueError(msg)

    data = json.loads(content)
    data["product_name"] = name
    data["price"] = price
    return data
