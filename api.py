"""Опциональный HTTP API для генерации отчётов (Flask)."""

from flask import Flask, jsonify, request
from openai import APIError

from utils.ai_processor import (
    process_design_order_with_ai,
    process_dialog_with_ai,
    process_product_card_with_ai,
)
from utils.errors import OPENAI_CLIENT_ERRORS, format_api_error
from utils.image_generator import VALID_QUALITIES, generate_image
from utils.logging_config import get_logger, setup_logging
from utils.pdf_generator import generate_report_pdf

setup_logging()
logger = get_logger(__name__)

app = Flask(__name__)

VALID_TYPES = frozenset({"client", "design", "product"})


def _get_transcript() -> str:
    if request.is_json:
        return (request.get_json(silent=True) or {}).get("transcript", "")
    return request.form.get("transcript", "")


def _get_json_field(key: str) -> str:
    if request.is_json:
        return (request.get_json(silent=True) or {}).get(key, "")
    return request.form.get(key, "")


def _error_response(message: str, status: int):
    logger.warning("Ответ %d: %s", status, message)
    return jsonify({"error": message}), status


@app.post("/api/report")
def create_report():
    report_type = (request.args.get("type") or "client").strip()
    logger.info("POST /api/report type=%s", report_type)

    if report_type not in VALID_TYPES:
        return _error_response("type: client, design или product", 400)

    try:
        if report_type == "client":
            text = (_get_transcript() or "").strip()
            if not text:
                return _error_response("Поле transcript обязательно", 400)
            report_data = process_dialog_with_ai(text)
            pdf_path = generate_report_pdf(report_data, report_type="client")

        elif report_type == "design":
            text = (_get_transcript() or "").strip()
            if not text:
                return _error_response("Поле transcript обязательно", 400)
            quality = (request.args.get("quality") or "medium").strip()
            if quality not in VALID_QUALITIES:
                return _error_response(
                    f"quality: {', '.join(sorted(VALID_QUALITIES))}",
                    400,
                )
            report_data = process_design_order_with_ai(text)
            image_path = generate_image(
                report_data["image_prompt"],
                quality,
                prefix="design",
            )
            pdf_path = generate_report_pdf(
                report_data,
                report_type="design",
                image_path=image_path,
            )

        else:
            name = (_get_json_field("name") or "").strip()
            price = (_get_json_field("price") or "").strip()
            if not name or not price:
                return _error_response("Поля name и price обязательны", 400)
            quality = (request.args.get("quality") or "medium").strip()
            if quality not in VALID_QUALITIES:
                return _error_response(
                    f"quality: {', '.join(sorted(VALID_QUALITIES))}",
                    400,
                )
            report_data = process_product_card_with_ai(name, price)
            image_path = generate_image(
                report_data["image_prompt"],
                quality,
                prefix="product",
            )
            pdf_path = generate_report_pdf(
                report_data,
                report_type="product",
                image_path=image_path,
            )

    except ValueError as exc:
        return _error_response(str(exc), 400)
    except (RuntimeError, OSError) as exc:
        logger.exception("Ошибка формирования отчёта")
        return _error_response(str(exc), 500)
    except APIError as exc:
        logger.exception("Ошибка API OpenAI")
        return _error_response(format_api_error(exc), 502)
    except OPENAI_CLIENT_ERRORS as exc:
        logger.exception("Ошибка соединения с API")
        return _error_response(f"Ошибка соединения с API: {exc}", 502)

    logger.info("Отчёт создан: %s", pdf_path)
    return jsonify(
        {
            "message": f"Отчёт успешно создан: {pdf_path}",
            "path": str(pdf_path),
            "type": report_type,
            "data": report_data,
        }
    )


if __name__ == "__main__":
    logger.info("Запуск Flask API на 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
