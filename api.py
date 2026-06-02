"""Опциональный HTTP API для генерации отчётов (Flask)."""

from flask import Flask, jsonify, request

from utils.ai_processor import process_design_order_with_ai, process_dialog_with_ai
from utils.image_generator import VALID_QUALITIES, generate_design_image
from utils.pdf_generator import generate_report_pdf

app = Flask(__name__)


def _get_transcript() -> str:
    if request.is_json:
        return (request.get_json(silent=True) or {}).get("transcript", "")
    return request.form.get("transcript", "")


@app.post("/api/report")
def create_report():
    text = (_get_transcript() or "").strip()
    if not text:
        return jsonify({"error": "Поле transcript обязательно"}), 400

    report_type = (request.args.get("type") or "client").strip()
    if report_type not in ("client", "design"):
        return jsonify({"error": "type должен быть client или design"}), 400

    try:
        if report_type == "client":
            report_data = process_dialog_with_ai(text)
            pdf_path = generate_report_pdf(report_data, report_type="client")
        else:
            quality = (request.args.get("quality") or "medium").strip()
            if quality not in VALID_QUALITIES:
                return jsonify({"error": f"quality: {', '.join(sorted(VALID_QUALITIES))}"}), 400
            report_data = process_design_order_with_ai(text)
            image_path = generate_design_image(report_data["image_prompt"], quality)
            pdf_path = generate_report_pdf(
                report_data,
                report_type="design",
                image_path=image_path,
            )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "message": f"Отчёт успешно создан: {pdf_path}",
            "path": str(pdf_path),
            "type": report_type,
            "data": report_data,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
