#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, cast

try:
    import yaml
    from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
    from markupsafe import Markup, escape
except ImportError as exc:
    missing = exc.name or "dependency"
    raise SystemExit(
        f"Missing {missing}. Install dependencies with: "
        "python -m pip install jinja2 pyyaml"
    ) from exc

ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "template"
VIEW_FILE = ROOT / "views" / "public.yaml"
OUTPUT_FILE = ROOT / "index.html"
BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")
UNDERLINE_PATTERN = re.compile(r"__(.+?)__")


def render_inline_markup(raw_text: str) -> Markup:
    """Render the small, intentional markup supported by view YAML files.

    Supported syntax:
    - ``\\n``: line break
    - ``**text**``: bold
    - ``__text__``: underline
    """
    formatted = str(escape(raw_text))
    formatted = BOLD_PATTERN.sub(r"<strong>\1</strong>", formatted)
    formatted = UNDERLINE_PATTERN.sub(r"<u>\1</u>", formatted)
    formatted = formatted.replace("\\n", "<br>\n")
    return Markup(formatted)


def prepare_view_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    data = deepcopy(raw_data)
    nodes = data.get("nodes", [])
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, dict):
                continue
            descriptions = node.get("desc", {})
            if isinstance(descriptions, dict):
                node["desc_html"] = {
                    language: str(render_inline_markup(text))
                    for language, text in descriptions.items()
                    if isinstance(text, str)
                }
    return data


def main() -> int:
    if not VIEW_FILE.is_file():
        print(f"View not found: {VIEW_FILE}", file=sys.stderr)
        return 1

    raw_data = cast(
        Dict[str, Any],
        yaml.safe_load(VIEW_FILE.read_text(encoding="utf-8")) or {},
    )
    data = prepare_view_data(raw_data)
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(("html", "xml")),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["inline_markup"] = render_inline_markup
    html = env.get_template("index.html.jinja").render(**data)
    OUTPUT_FILE.write_text(html.rstrip() + "\n", encoding="utf-8")
    print(f"Generated {OUTPUT_FILE.relative_to(ROOT)} from {VIEW_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
