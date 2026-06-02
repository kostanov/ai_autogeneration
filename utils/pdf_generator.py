from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
REPORTS_DIR = PROJECT_ROOT / "reports"

TEMPLATE_BY_TYPE = {
    "client": "report_template.html",
    "design": "design_report_template.html",
}
PREFIX_BY_TYPE = {
    "client": "report",
    "design": "design_report",
}


def generate_report_pdf(
    data: dict[str, str],
    *,
    report_type: str = "client",
    image_path: Path | None = None,
) -> Path:
    if report_type not in TEMPLATE_BY_TYPE:
        msg = f"Неизвестный тип отчёта: {report_type}"
        raise ValueError(msg)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(TEMPLATE_BY_TYPE[report_type])

    context = dict(data)
    if report_type == "design":
        context["image_uri"] = (
            image_path.resolve().as_uri() if image_path and image_path.exists() else ""
        )

    html_content = template.render(**context)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{PREFIX_BY_TYPE[report_type]}_{timestamp}.pdf"
    output_path = REPORTS_DIR / filename

    HTML(string=html_content, base_url=str(PROJECT_ROOT)).write_pdf(output_path)
    return output_path
