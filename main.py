import argparse
import sys
from pathlib import Path

from openai import APIError

from utils.ai_processor import (
    process_design_order_with_ai,
    process_dialog_with_ai,
    process_product_card_with_ai,
)
from utils.errors import OPENAI_CLIENT_ERRORS, format_api_error
from utils.image_generator import generate_image
from utils.logging_config import get_logger, setup_logging
from utils.pdf_generator import generate_report_pdf

REPORT_TYPES = ("client", "design", "product")
IMAGE_QUALITIES = ("low", "medium", "high")

logger = get_logger(__name__)


def read_transcript(file_path: Path | None) -> str:
    if file_path:
        logger.info("Чтение транскрибации из файла: %s", file_path)
        if not file_path.is_file():
            msg = f"Файл не найден: {file_path}"
            raise FileNotFoundError(msg)
        text = file_path.read_text(encoding="utf-8").strip()
        logger.info("Загружено %d символов", len(text))
        return text

    if sys.stdin.isatty():
        print("Введите транскрибацию диалога (завершите Ctrl+D):")
    logger.info("Чтение транскрибации из stdin")
    text = sys.stdin.read().strip()
    logger.info("Загружено %d символов", len(text))
    return text


def run_client_report(text: str, *, mock: bool) -> Path:
    logger.info("Запуск отчёта type=client, mock=%s", mock)
    report_data = process_dialog_with_ai(text, mock=mock)
    return generate_report_pdf(report_data, report_type="client")


def run_design_report(text: str, *, mock: bool, quality: str) -> Path:
    logger.info("Запуск отчёта type=design, mock=%s, quality=%s", mock, quality)
    report_data = process_design_order_with_ai(text, mock=mock)
    image_path = None
    if not mock:
        image_path = generate_image(
            report_data["image_prompt"],
            quality,
            prefix="design",
        )
    return generate_report_pdf(
        report_data,
        report_type="design",
        image_path=image_path,
    )


def run_product_report(
    name: str,
    price: str,
    *,
    mock: bool,
    quality: str,
) -> Path:
    logger.info(
        "Запуск отчёта type=product, mock=%s, quality=%s, товар=%r",
        mock,
        quality,
        name,
    )
    report_data = process_product_card_with_ai(name, price, mock=mock)
    image_path = None
    if not mock:
        image_path = generate_image(
            report_data["image_prompt"],
            quality,
            prefix="product",
        )
    return generate_report_pdf(
        report_data,
        report_type="product",
        image_path=image_path,
    )


def run(
    file_path: Path | None,
    *,
    report_type: str,
    mock: bool,
    quality: str,
    product_name: str | None,
    product_price: str | None,
) -> Path:
    if report_type == "product":
        if not product_name or not product_price:
            msg = "Для type=product укажите --name и --price"
            raise ValueError(msg)
        return run_product_report(
            product_name,
            product_price,
            mock=mock,
            quality=quality,
        )

    text = read_transcript(file_path)
    if not text:
        msg = "Транскрибация пуста. Укажите файл или введите текст."
        raise ValueError(msg)

    if report_type == "client":
        return run_client_report(text, mock=mock)
    return run_design_report(text, mock=mock, quality=quality)


def handle_error(exc: BaseException) -> None:
    if isinstance(exc, APIError):
        print(format_api_error(exc), file=sys.stderr)
    elif isinstance(exc, OPENAI_CLIENT_ERRORS):
        print(f"Ошибка соединения с API: {exc}", file=sys.stderr)
    elif isinstance(exc, FileNotFoundError):
        print(f"Ошибка: {exc}", file=sys.stderr)
    elif isinstance(exc, (ValueError, OSError, RuntimeError)):
        print(f"Ошибка: {exc}", file=sys.stderr)
    else:
        logger.exception("Непредвиденная ошибка")
        print(f"Непредвиденная ошибка: {exc}", file=sys.stderr)


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(
        description="AI Client Report Generator — PDF-отчёты и карточки товаров",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Путь к файлу с транскрибацией (client, design)",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=REPORT_TYPES,
        default="client",
        help="Тип: client — диалог; design — дизайн сайта; product — карточка товара",
    )
    parser.add_argument(
        "--name",
        help="Название товара (для type=product)",
    )
    parser.add_argument(
        "--price",
        help="Цена товара (для type=product)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        choices=IMAGE_QUALITIES,
        default="medium",
        help="Качество изображения (design, product)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Демо-режим без API",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Подробные логи (уровень DEBUG)",
    )
    args = parser.parse_args()

    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Включён режим DEBUG")

    logger.info(
        "Старт: type=%s, mock=%s, file=%s",
        args.type,
        args.mock,
        args.file,
    )

    try:
        pdf_path = run(
            args.file,
            report_type=args.type,
            mock=args.mock,
            quality=args.quality,
            product_name=args.name,
            product_price=args.price,
        )
    except (
        ValueError,
        OSError,
        RuntimeError,
        FileNotFoundError,
        *OPENAI_CLIENT_ERRORS,
    ) as exc:
        handle_error(exc)
        sys.exit(1)
    except Exception as exc:
        handle_error(exc)
        sys.exit(1)

    logger.info("Готово: %s", pdf_path)
    print(f"Отчёт успешно создан: {pdf_path}")


if __name__ == "__main__":
    main()
