# AI Client Report Generator

Автоматическое формирование PDF-отчётов по диалогам с клиентами с помощью OpenAI, Jinja2 и WeasyPrint.

## Структура

```
├── main.py              # CLI: транскрибация → ИИ → PDF
├── api.py               # опциональный Flask API
├── templates/
│   ├── report_template.html
│   └── design_report_template.html
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

# демо без API
just demo
just demo-design

# HTTP API
just api
# POST /api/report?type=client  {"transcript": "..."}
# POST /api/report?type=design&quality=high  {"transcript": "..."}
```

## Команды

| Команда | Описание |
|---------|----------|
| `just` | список команд |
| `just run` | генерация отчёта (`-t client` / `-t design`, `-q` для качества картинки) |
| `just demo` | демо-отчёт по диалогу |
| `just demo-design` | демо-отчёт по дизайну (без картинки) |
| `just sample-design` | полный отчёт design с API |
| `just api` | Flask API |
| `just lint` | проверка ruff |
| `just fix` | автоисправление |
| `just format` | форматирование |
