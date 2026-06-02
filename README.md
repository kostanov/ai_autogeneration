# AI Client Report Generator

Автоматическое формирование PDF-отчётов по диалогам с клиентами с помощью OpenAI, Jinja2 и WeasyPrint.

## Структура

```
├── main.py                    # CLI: три типа отчётов (client / design / product)
├── api.py                     # Flask API (POST /api/report)
├── justfile                   # команды just (text, image, product, run, api, lint…)
├── pyproject.toml             # зависимости (uv)
├── templates/
│   ├── report_template.html       # отчёт по диалогу
│   ├── design_report_template.html # заказ дизайна сайта
│   └── product_card_template.html  # карточка товара
├── reports/                   # готовые PDF (*.pdf)
│   └── images/                # сгенерированные фоны (*.png)
├── utils/
│   ├── ai_processor.py        # запросы к чат-модели (OPENAI_MODEL)
│   ├── image_generator.py     # генерация изображений (gpt-image-1-mini)
│   ├── pdf_generator.py       # HTML → PDF (WeasyPrint)
│   ├── errors.py              # обработка ошибок API
│   └── logging_config.py      # настройка логирования
├── samples/
│   ├── dialog_example.txt         # пример для client
│   └── design_dialog_example.txt  # пример для design
├── .env                       # ключи и настройки (не в git)
├── .env.example
└── requirements.txt           # список зависимостей (дубль pyproject)
```

## Установка

```bash
uv sync
cp .env.example .env
# укажите OPENAI_API_KEY в .env
```

Для WeasyPrint на Linux могут понадобиться системные пакеты (cairo, pango). Fedora:

```bash
sudo dnf install cairo pango gdk-pixbuf2 libffi
```

## Запуск

```bash
# отчёт по диалогу (client, type по умолчанию)
just text

# отчёт по заказу дизайна с макетом (design)
just image
just image high          # quality: low | medium | high

# карточка товара для маркетплейса (product)
just product

# произвольные аргументы CLI
just run -- -f samples/dialog_example.txt
just run -- -t design -q medium -f samples/design_dialog_example.txt
just run -- -t product --name "Наушники" --price "4 990 ₽" -q medium
just run -- -t product --name "..." --price "..." --mock   # без API
just run -- -v --mock -f samples/dialog_example.txt        # подробные логи

# HTTP API
just api
# POST /api/report?type=client  {"transcript": "..."}
# POST /api/report?type=design&quality=high  {"transcript": "..."}
# POST /api/report?type=product&quality=medium  {"name": "...", "price": "..."}
```

## Команды

| Команда | Описание |
|---------|----------|
| `just` | список рецептов |
| `just run -- …` | запуск `main.py` с любыми аргументами (`-t`, `-f`, `--name`, `--price`, `-q`, `--mock`, `-v`) |
| `just text` | отчёт **client** из `samples/dialog_example.txt` |
| `just image` | отчёт **design** из `samples/design_dialog_example.txt` (quality по умолчанию `medium`) |
| `just image high` | то же с `quality=high` |
| `just product` | карточка **product** (наушники, 4 990 ₽) |
| `just api` | Flask API на порту 5000 |
| `just lint` | `ruff check` |
| `just fix` | `ruff check --fix` |
| `just format` | `ruff format` |
