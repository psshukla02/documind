#!/usr/bin/env python3
"""Build docs/DocuMind_Documentation.pdf from the Markdown files in docs/.

Strategy:
    1. Concatenate files in a fixed, rubric-aligned order.
    2. Preprocess each file:
        - Strip Mermaid code fences → replace with a note + the raw source
          inside a verbatim block so the reader can still see the structure.
        - Bump heading levels so each section starts at H1 in the merged doc.
    3. Run pandoc with xelatex for proper PDF output (code highlighting,
       tables, TOC).
    4. Fallback: if pandoc isn't available, try a weasyprint path.

Run:
    python scripts/build_pdf.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "DocuMind_Documentation.pdf"
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)
MERGED = BUILD / "_merged.md"

# Order chosen to match the rubric's required section order.
SECTIONS: list[tuple[str, str]] = [
    ("_cover.md",        None),                         # cover + TOC intro
    ("architecture.md",  "System Architecture"),
    ("implementation.md","Implementation Details"),
    ("agent.md",         "Autonomous Research Agent"),
    ("performance.md",   "Performance Metrics"),
    ("challenges.md",    "Challenges and Solutions"),
    ("ethics.md",        "Ethical Considerations"),
    ("future_work.md",   "Future Improvements"),
]

_MERMAID_BLOCK = re.compile(
    r"```mermaid\s*\n(?P<body>.*?)\n```",
    re.DOTALL,
)

# Emojis and a few Unicode symbols the default LaTeX fonts don't ship with.
# We replace them with short ASCII substitutes so the PDF doesn't render
# empty boxes. Add to this map as needed.
_EMOJI_MAP = {
    "✅": "[OK]",
    "✓": "[v]",
    "❌": "[X]",
    "⚠️": "[!]",
    "⚠": "[!]",
    "🔥": "[!]",
    "🧠": "",
    "💬": "",
    "📚": "",
    "📝": "",
    "🧪": "",
    "📈": "",
    "🤖": "",
    "🚀": "",
    "🧭": "",
    "🔎": "",
    "📋": "",
    "⬇️": "",
    "📄": "",
    "⚖️": "",
    "⏭️": "",
    "🏁": "",
    "🎥": "",
    "🌐": "",
    "🔐": "",
    "🎨": "",
    "🎯": "",
    "⚙️": "",
    "🧩": "",
    "🏗️": "",
    "🔧": "",
    "📌": "",
    "📂": "",
    "📊": "",
    "💡": "",
    "👋": "",
    "≤": "<=",
    "≥": ">=",
    "→": "->",
    "←": "<-",
    "…": "...",
    "—": "--",
    "–": "-",
    "“": '"', "”": '"',
    "‘": "'", "’": "'",
}


def _strip_emojis(text: str) -> str:
    for k, v in _EMOJI_MAP.items():
        text = text.replace(k, v)
    # Catch-all: remove any remaining characters in the emoji surrogate ranges.
    text = re.sub(
        "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F1FF]",
        "",
        text,
    )
    return text


def preprocess(md: str) -> str:
    """Replace Mermaid fences with a short note + the source as plain code.

    Pandoc/xelatex cannot render Mermaid. Rather than silently dropping the
    diagram, we keep the source visible so readers can paste it into
    https://mermaid.live/ if they want the rendered version. We also strip
    emojis that the default LaTeX fonts don't support.
    """
    def _sub(m):
        body = m.group("body").strip()
        return (
            "\n> **Diagram (Mermaid source below — render at "
            "https://mermaid.live/ to view).**\n\n"
            "```\n"
            f"{body}\n"
            "```\n"
        )

    md = _MERMAID_BLOCK.sub(_sub, md)
    md = _strip_emojis(md)
    return md


def merge() -> Path:
    parts: list[str] = []
    for filename, h1_title in SECTIONS:
        src = DOCS / filename
        if not src.exists():
            print(f"  ! skipped missing {filename}", file=sys.stderr)
            continue
        text = src.read_text(encoding="utf-8")
        text = preprocess(text)

        # Cover page already has its own YAML front-matter + headings.
        if filename == "_cover.md":
            parts.append(text)
            continue

        # Prepend a page break + H1 so each section starts cleanly.
        header = f"\n\\clearpage\n\n# {h1_title}\n\n" if h1_title else ""
        parts.append(header + text + "\n")

    merged = "\n".join(parts)
    MERGED.write_text(merged, encoding="utf-8")
    print(f"  merged {len(SECTIONS)} files → {MERGED} ({len(merged):,} chars)")
    return MERGED


def build_with_pandoc(merged: Path) -> bool:
    if not shutil.which("pandoc"):
        return False

    engine = None
    for cand in ("xelatex", "pdflatex", "wkhtmltopdf", "weasyprint"):
        if shutil.which(cand):
            engine = cand
            break
    if not engine:
        print("  ! pandoc found but no PDF engine (xelatex/wkhtmltopdf/weasyprint)")
        return False

    cmd = [
        "pandoc",
        str(merged),
        "-o", str(OUT),
        "--toc",
        "--toc-depth=2",
        f"--pdf-engine={engine}",
        "--highlight-style=tango",
        "-V", "colorlinks=true",
    ]
    print(f"  running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ! pandoc failed (exit {e.returncode})")
        return False


def build_with_weasyprint(merged: Path) -> bool:
    try:
        import markdown
        from weasyprint import CSS, HTML
    except ImportError:
        print("  ! weasyprint/markdown not installed; `pip install weasyprint markdown`")
        return False

    html_body = markdown.markdown(
        merged.read_text(encoding="utf-8"),
        extensions=["fenced_code", "tables", "toc"],
    )
    html = f"""<html><head><meta charset="utf-8">
    <style>
    body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 780px; margin: 2em auto; padding: 0 1em; color: #222; }}
    h1,h2,h3 {{ color: #1a3a6b; }}
    code, pre {{ font-family: 'SF Mono', Menlo, monospace; }}
    pre {{ background: #f5f5f7; padding: 0.8em; border-radius: 6px; overflow-x: auto; font-size: 0.85em; }}
    code {{ background: #f5f5f7; padding: 0.1em 0.3em; border-radius: 3px; font-size: 0.9em; }}
    table {{ border-collapse: collapse; margin: 1em 0; }}
    th, td {{ border: 1px solid #ddd; padding: 0.4em 0.7em; }}
    th {{ background: #f0f0f0; }}
    </style></head><body>{html_body}</body></html>"""
    HTML(string=html).write_pdf(str(OUT))
    return True


def main() -> int:
    print(f"→ building {OUT.relative_to(ROOT)}")
    merged = merge()

    if build_with_pandoc(merged):
        ok = True
    elif build_with_weasyprint(merged):
        ok = True
    else:
        print("! No working PDF backend.", file=sys.stderr)
        print("  Install pandoc + a LaTeX engine, OR `pip install weasyprint markdown`.")
        return 1

    size = OUT.stat().st_size
    print(f"✓ wrote {OUT} ({size/1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
