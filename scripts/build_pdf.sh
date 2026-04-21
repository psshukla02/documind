#!/usr/bin/env bash
# Build docs/DocuMind_Documentation.pdf. Prefers pandoc; falls back to
# a Python (weasyprint) path. Run from the repo root or this folder.
set -e
cd "$(dirname "$0")/.."
python3 scripts/build_pdf.py
