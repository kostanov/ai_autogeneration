import argparse
import sys
from pathlib import Path

from openai import APIError

from utils.ai_processor import process_design_order_with_ai, process_dialog_with_ai
from utils.image_generator import generate_design_image
from utils.pdf_generator import generate_report_pdf

REPORT_TYPES = ("client", "design")
IMAGE_QUALITIES = ("low", "medium", "high")


def read_transcript(file_path: Path | None) -> str:
    if file_path:
        return file_path.read_text(encoding="utf-8").strip()

    if sys.stdin.isatty():
        print("Введите транскрибацию диалога (завершите Ctrl+D):")
    return sys.stdin.read().strip()


def run_client_report(text: str, *, mock: bool) -> Path:
    report_data = process_dialog_with_ai(text, mock=mock)
    return generate_report_pdf(report_data, report_type="client")


def run_design_report(text: str, *, mock: bool, quality: str) -> Path:
    report_data = process_design_order_with_ai(text, mock=mock)
    image_path = None
    if not mock:
        image_path = generate_design_image(report_data["image_prompt"], quality)
    return generate_report_pdf(
        report_data,
        report_type="design",
        image_path=image_path,
    )


def run(
    file_path: Path | None,
    *,
    report_type: str,
    mock: bool,
    quality: str,
) -> Path:
    text = read_transcript(file_path)
    if not text:
        msg = "Транскрибация пуста. Укажите файл или введите текст."
        raise ValueError(msg)

    if report_type == "client":
        return run_client_report(text, mock=mock)
    return run_design_report(text, mock=mock, quality=quality)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Client Report Generator — PDF-отчёты по диалогам с клиентами",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Путь к файлу с транскрибацией диалога",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=REPORT_TYPES,
        default="client",
        help="Тип отчёта: client — диалог; design — заказ дизайна сайта с макетом",
    )
    parser.add_argument(
        "-q",
        "--quality",
        choices=IMAGE_QUALITIES,
        default="medium",
        help="Качество генерации изображения (только для type=design)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Демо-режим без API (фиксированные данные отчёта)",
    )
    args = parser.parse_args()

    try:
        pdf_path = run(
            args.file,
            report_type=args.type,
            mock=args.mock,
            quality=args.quality,
        )
    except (ValueError, OSError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        sys.exit(1)
    except APIError as exc:
        hint = ""
        body = getattr(exc, "body", None) or {}
        code = (body.get("error") or {}).get("code", "")
        if code == "unsupported_country_region_territory":
            hint = (
                " Укажите OPENAI_BASE_URL в .env (прокси-провайдер) "
                "или запустите с --mock."
            )
        print(f"Ошибка API: {exc}{hint}", file=sys.stderr)
        sys.exit(1)

    print(f"Отчёт успешно создан: {pdf_path}")


if __name__ == "__main__":
    main()
