#!/usr/bin/env python3
"""
Render PlantUML diagrams to SVG and PDF via Kroki.
https://docs.kroki.io/kroki/setup/usage/

Vector-only pipeline (no PNG):
  1. POST Kroki /plantuml/svg  (skinparam shadowing false — avoids GraalVM crash)
  2. Inject offset shadow rectangles (pure vector, svglib-safe)
  3. Convert SVG → PDF (cairosvg / Inkscape / svglib)
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

DEFAULT_KROKI_URL = os.environ.get("KROKI_URL", "https://kroki.io")
KROKI_TIMEOUT = int(os.environ.get("KROKI_TIMEOUT", "120"))
FONT_SCALE = float(os.environ.get("PUML_FONT_SCALE", "1.0"))

SCRIPT_DIR = Path(__file__).resolve().parent
PUML_DIR = SCRIPT_DIR.parent / "diagrams" / "puml"
RENDERED_DIR = PUML_DIR / "rendered"


def resolve_includes(puml_text: str, base_dir: Path) -> str:
    """Inline local !include directives for a self-contained diagram."""
    lines_out: list[str] = []
    for line in puml_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("!include"):
            parts = stripped.split()
            if len(parts) >= 2:
                inc_path = base_dir / parts[1]
                if inc_path.exists():
                    lines_out.append(inc_path.read_text(encoding="utf-8"))
                else:
                    raise FileNotFoundError(f"Include not found: {inc_path}")
            continue
        lines_out.append(line)
    return "\n".join(lines_out) + "\n"


def fetch_kroki(puml_text: str, fmt: str, kroki_base: str) -> bytes:
    """Fetch rendered diagram bytes from Kroki (POST plain text)."""
    url = f"{kroki_base.rstrip('/')}/plantuml/{fmt}"
    response = requests.post(
        url,
        data=puml_text.encode("utf-8"),
        headers={"Content-Type": "text/plain"},
        timeout=KROKI_TIMEOUT,
    )
    if response.status_code >= 400:
        snippet = response.text[:800] if response.text else "(empty body)"
        raise RuntimeError(f"Kroki {fmt} HTTP {response.status_code}: {snippet}")
    return response.content


def fetch_kroki_json(puml_text: str, fmt: str, kroki_base: str) -> bytes:
    """Fallback: Kroki JSON API."""
    url = f"{kroki_base.rstrip('/')}/"
    payload = {
        "diagram_source": puml_text,
        "diagram_type": "plantuml",
        "output_format": fmt,
    }
    response = requests.post(url, json=payload, timeout=KROKI_TIMEOUT)
    if response.status_code >= 400:
        snippet = response.text[:800] if response.text else "(empty body)"
        raise RuntimeError(f"Kroki JSON {fmt} HTTP {response.status_code}: {snippet}")
    return response.content


def render_diagram(puml_text: str, fmt: str, kroki_base: str) -> bytes:
    try:
        return fetch_kroki(puml_text, fmt, kroki_base)
    except Exception as primary_err:
        try:
            return fetch_kroki_json(puml_text, fmt, kroki_base)
        except Exception:
            raise primary_err


def inject_svg_shadows(svg_text: str) -> str:
    """
    Add embossed depth via offset shadow rectangles (pure vector).
    Works with svglib PDF conversion; avoids PlantUML GraalVM shadow crash
    and feDropShadow filters that svglib strips.
    """
    if "hsp-shadow-clone" in svg_text:
        return svg_text

    rect_pat = re.compile(
        r'<rect fill="(#[0-9A-Fa-f]{6})" height="([\d.]+)"'
        r'(?:[^>]*)?rx="([\d.]+)"(?:[^>]*)?'
        r'width="([\d.]+)"(?:[^>]*)?x="([\d.]+)" y="([\d.]+)"(?:[^/]*)/?>'
    )

    def _shadow_block(match: re.Match[str]) -> str:
        block = match.group(0)
        if "hsp-shadow-clone" in block:
            return block
        m = rect_pat.search(block)
        if not m:
            return block
        _fill, h, rx, w, x, y = m.groups()
        sx = float(x) + 2.0
        sy = float(y) + 2.5
        shadow = (
            f'<rect class="hsp-shadow-clone" fill="#000000" opacity="0.20" '
            f'height="{h}" rx="{rx}" ry="{rx}" width="{w}" '
            f'x="{sx}" y="{sy}" pointer-events="none"/>'
        )
        return block.replace(m.group(0), shadow + m.group(0), 1)

    for cls in ("entity", "participant", "cluster", "note"):
        svg_text = re.sub(
            rf'(<g class="{cls}"[^>]*>.*?</g>)',
            _shadow_block,
            svg_text,
            flags=re.DOTALL,
        )

    svg_text = inject_flow_shadows(svg_text)
    return svg_text


SHADOW_OFFSET_X = 2.0
SHADOW_OFFSET_Y = 2.5
SHADOW_OPACITY = 0.20
FLOW_SHADOW_FILLS = frozenset({"#EDF2F7", "#FFFAF0", "#FFFFF0", "#F7FAFC"})


def _rect_shadow_tag(h: str, rx: str, w: str, x: str, y: str) -> str:
    return (
        f'<rect class="hsp-shadow-clone" fill="#000000" opacity="{SHADOW_OPACITY}" '
        f'height="{h}" rx="{rx}" ry="{rx}" width="{w}" '
        f'x="{float(x) + SHADOW_OFFSET_X}" y="{float(y) + SHADOW_OFFSET_Y}" '
        f'pointer-events="none"/>'
    )


def inject_flow_shadows(svg_text: str) -> str:
    """Shadows for activity/state shapes not wrapped in PlantUML entity groups."""
    dtype = re.search(r'data-diagram-type="([A-Z]+)"', svg_text)
    if not dtype or dtype.group(1) not in ("ACTIVITY", "STATE"):
        return svg_text

    rect_re = re.compile(
        r'<rect fill="(#[0-9A-Fa-f]{6})" height="([\d.]+)"'
        r'(?:[^>]*)?rx="([\d.]+)"(?:[^>]*)?'
        r'width="([\d.]+)"(?:[^>]*)?x="([\d.]+)" y="([\d.]+)"(?:[^/]*)/?>'
    )

    def _shadow_rect(match: re.Match[str]) -> str:
        rect = match.group(0)
        if "hsp-shadow-clone" in rect:
            return rect
        fill, h, rx, w, x, y = match.groups()
        if fill.upper() not in FLOW_SHADOW_FILLS:
            return rect
        if float(w) < 20 or float(h) < 12:
            return rect
        return _rect_shadow_tag(h, rx, w, x, y) + rect

    svg_text = rect_re.sub(_shadow_rect, svg_text)

    poly_re = re.compile(
        r'(<polygon fill="(#[0-9A-Fa-f]{6})")([^>]*?points="([^"]+)"([^/]*)/>)'
    )

    def _shadow_polygon(match: re.Match[str]) -> str:
        poly = match.group(0)
        if "hsp-shadow-clone" in poly:
            return poly
        if match.group(2).upper() != "#FFFAF0":
            return poly
        head, _fill, mid, points, tail = match.groups()
        shadow = (
            f'<polygon class="hsp-shadow-clone" fill="#000000" opacity="{SHADOW_OPACITY}" '
            f'transform="translate({SHADOW_OFFSET_X},{SHADOW_OFFSET_Y})" '
            f'{mid}points="{points}"{tail}'
        )
        return shadow + poly

    svg_text = poly_re.sub(_shadow_polygon, svg_text)

    path_re = re.compile(
        r'(<path d="[^"]+" fill="(#[0-9A-Fa-f]{6})")([^/]*)/>'
    )

    def _shadow_path(match: re.Match[str]) -> str:
        path = match.group(0)
        if "hsp-shadow-clone" in path:
            return path
        if match.group(2).upper() != "#FFFFF0":
            return path
        head, _fill, tail = match.groups()
        shadow = (
            f'{head.replace(match.group(2), "#000000")} opacity="{SHADOW_OPACITY}" '
            f'class="hsp-shadow-clone" transform="translate({SHADOW_OFFSET_X},{SHADOW_OFFSET_Y})"'
            f'{tail}/>'
        )
        return shadow + path

    svg_text = path_re.sub(_shadow_path, svg_text)
    return svg_text


def boost_svg_typography(svg_text: str, scale: float = FONT_SCALE) -> str:
    """Scale SVG font sizes and enforce bold weight (printed legibility)."""
    if scale != 1.0:

        def _scale_font(match: re.Match[str]) -> str:
            size = float(match.group(1))
            return f'font-size="{size * scale:.4f}"'

        svg_text = re.sub(r'font-size="([0-9.]+)"', _scale_font, svg_text)

    svg_text = re.sub(
        r'(<text\b(?![^>]*font-weight)[^>]*)(>)',
        r'\1 font-weight="700"\2',
        svg_text,
    )
    return svg_text


def svg_to_pdf_cairosvg(svg_path: Path, pdf_path: Path) -> bool:
    try:
        import cairosvg
        cairosvg.svg2pdf(url=str(svg_path), write_to=str(pdf_path))
        return pdf_path.exists()
    except ImportError:
        return False
    except Exception as e:
        print(f"    cairosvg error: {e}")
        return False


def svg_to_pdf_svglib(svg_path: Path, pdf_path: Path) -> bool:
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPDF
        drawing = svg2rlg(str(svg_path))
        if drawing is None:
            return False
        renderPDF.drawToFile(drawing, str(pdf_path))
        return pdf_path.exists()
    except Exception:
        return False


def svg_to_pdf_inkscape(svg_path: Path, pdf_path: Path) -> bool:
    try:
        result = subprocess.run(
            ["inkscape", f"--export-pdf={pdf_path}", str(svg_path)],
            capture_output=True,
            timeout=60,
        )
        return result.returncode == 0 and pdf_path.exists()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def convert_svg_to_pdf(svg_path: Path, pdf_path: Path) -> bool:
    converters = [
        ("cairosvg", svg_to_pdf_cairosvg),
        ("Inkscape", svg_to_pdf_inkscape),
        ("svglib", svg_to_pdf_svglib),
    ]
    for name, fn in converters:
        print(f"    Trying {name}...", end=" ")
        if fn(svg_path, pdf_path):
            print("OK")
            return True
        print("not available")
    return False


def render_file(puml_path: Path, kroki_base: str) -> None:
    stem = puml_path.stem
    print(f"[{stem}]")

    puml_text = resolve_includes(puml_path.read_text(encoding="utf-8"), puml_path.parent)

    svg_path = RENDERED_DIR / f"{stem}.svg"
    pdf_path = RENDERED_DIR / f"{stem}.pdf"

    print(f"  Kroki SVG ({kroki_base})...", end=" ")
    try:
        svg_bytes = render_diagram(puml_text, "svg", kroki_base)
        if b"An error has occured" in svg_bytes or b"java.lang" in svg_bytes:
            raise RuntimeError("PlantUML error embedded in SVG response")
        svg_text = inject_svg_shadows(svg_bytes.decode("utf-8"))
        svg_text = boost_svg_typography(svg_text)
        svg_path.write_text(svg_text, encoding="utf-8")
        print(f"OK  ({len(svg_text)} chars -> {svg_path.name}, shadows + typography)")
    except Exception as e:
        print(f"FAILED: {e}")
        return

    print(f"  SVG → PDF (vector)...", end=" ")
    if convert_svg_to_pdf(svg_path, pdf_path):
        print(f"OK  ({pdf_path.stat().st_size} bytes -> {pdf_path.name})")
    else:
        print(f"FAILED: could not produce {pdf_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render PlantUML via Kroki (SVG→PDF, vector only)")
    parser.add_argument(
        "--kroki-url",
        default=DEFAULT_KROKI_URL,
        help=f"Kroki base URL (default: {DEFAULT_KROKI_URL})",
    )
    args = parser.parse_args()
    kroki_base = args.kroki_url.rstrip("/")

    RENDERED_DIR.mkdir(parents=True, exist_ok=True)

    puml_files = sorted(p for p in PUML_DIR.glob("*.puml") if not p.name.startswith("_"))
    if not puml_files:
        print(f"No .puml files found in {PUML_DIR}")
        sys.exit(0)

    print(f"Found {len(puml_files)} diagram(s) in {PUML_DIR}")
    print(f"Kroki endpoint: {kroki_base}  [vector SVG→PDF, no PNG]\n")
    errors = 0
    for puml_path in puml_files:
        try:
            render_file(puml_path, kroki_base)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            errors += 1
        print()

    if errors:
        sys.exit(1)
    print("Done.")


if __name__ == "__main__":
    main()
