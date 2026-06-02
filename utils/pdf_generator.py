from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from weasyprint import HTML

from utils.logging_config import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
REPORTS_DIR = PROJECT_ROOT / "reports"

TEMPLATE_BY_TYPE = {
    "client": "report_template.html",
    "design": "design_report_template.html",
    "product": "product_card_template.html",
}
PREFIX_BY_TYPE = {
    "client": "report",
    "design": "design_report",
    "product": "product_card",
}
IMAGE_REPORT_TYPES = frozenset({"design", "product"})


def generate_report_pdf(
    data: dict[str, str],
    *,
    report_type: str = "client",
    image_path: Path | None = None,
) -> Path:
    if report_type not in TEMPLATE_BY_TYPE:
        msg = f"Неизвестный тип отчёта: {report_type}"
        raise ValueError(msg)

    template_name = TEMPLATE_BY_TYPE[report_type]
    logger.info("Этап «сборка PDF»: тип=%s, шаблон=%s", report_type, template_name)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )

    try:
        template = env.get_template(template_name)
    except TemplateNotFound as exc:
        logger.error("Шаблон не найден: %s", template_name)
        msg = f"Шаблон отчёта не найден: {template_name}"
        raise ValueError(msg) from exc

    context = dict(data)
    if report_type in IMAGE_REPORT_TYPES:
        if image_path and image_path.exists():
            context["image_uri"] = image_path.resolve().as_uri()
            logger.info("Этап «сборка PDF»: фоновое изображение %s", image_path)
        else:
            context["image_uri"] = ""
            logger.warning("Этап «сборка PDF»: изображение не задано или отсутствует")

    try:
        html_content = template.render(**context)
    except Exception as exc:
        log_and_reraise_pdf("рендер HTML", exc)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{PREFIX_BY_TYPE[report_type]}_{timestamp}.pdf"
    output_path = REPORTS_DIR / filename

    try:
        HTML(string=html_content, base_url=str(PROJECT_ROOT)).write_pdf(output_path)
    except Exception as exc:
        log_and_reraise_pdf("конвертация в PDF (WeasyPrint)", exc)

    logger.info("Этап «сборка PDF»: готово %s", output_path)
    return output_path


def log_and_reraise_pdf(stage: str, exc: Exception) -> None:
    logger.exception("Ошибка на этапе «%s»: %s", stage, exc)
    msg = f"Не удалось сформировать PDF: {stage}"
    raise RuntimeError(msg) from exc
