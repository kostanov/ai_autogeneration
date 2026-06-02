# AI Client Report Generator

Автоматическое формирование PDF-отчётов по диалогам с клиентами с помощью OpenAI, Jinja2 и WeasyPrint.

## Структура

```
├── main.py              # CLI: транскрибация → ИИ → PDF
├── api.py               # опциональный Flask API
├── templates/
│   ├── report_template.html
│   ├── design_report_template.html
│   └── product_card_template.html
├── reports/             # готовые PDF и images/
├── utils/
│   ├── ai_processor.py
│   ├── image_generator.py
│   └── pdf_generator.py
├── samples/             # примеры транскрибаций
├── .env                 # API-ключ (не в git)
└── requirements.txt
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
# отчёт по диалогу (client)
just run -- -f samples/dialog_example.txt

# отчёт по заказу дизайна с генерацией макета (design)
just run -- -t design -q medium -f samples/design_dialog_example.txt

# карточка товара для маркетплейса (product)
just run -- -t product --name "Наушники TWS Pro X" --price "4 990 ₽" -q medium
just demo-product

# HTTP API
just api
# POST /api/report?type=client  {"transcript": "..."}
# POST /api/report?type=design&quality=high  {"transcript": "..."}
# POST /api/report?type=product&quality=medium  {"name": "...", "price": "..."}
```

## Команды

| Команда | Описание |
|---------|----------|
| `just` | список команд |
| `just run` | генерация (`-t client` / `design` / `product`, `-q` для картинки) |
| `just demo-product` | демо карточки товара (без API) |
| `just product` | карточка с API: `just product "Название" "1 990 ₽"` |
| `just api` | Flask API |
| `just lint` | проверка ruff |
| `just fix` | автоисправление |
| `just format` | форматирование |
