"""Buat dashboard offline dari hasil evaluator; tidak membutuhkan package tambahan."""

import json
from pathlib import Path


def render_dashboard(report, destination):
    """Embed data dengan escaping agar teks dokumen tidak menjadi markup/script."""
    template = Path(__file__).with_name("chunking_dashboard.html").read_text(encoding="utf-8")
    data = json.dumps(report, ensure_ascii=False).replace("<", "\\u003c")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(template.replace("__REPORT_JSON__", data), encoding="utf-8")
    return destination


if __name__ == "__main__":
    from evaluate_chunking import REPORT_DIR, evaluate_all
    print(render_dashboard(evaluate_all(), REPORT_DIR / "chunking_quality.html"))
