#!/usr/bin/env python3
"""
Rebuild index.html by combining individual slide files from ../Presentation/.

Usage:
    python3 build.py

Reads:
    ../Presentation/slide_*.html

Writes:
    ./index.html
"""

import re
import os
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.normpath(os.path.join(HERE, "..", "Presentation"))
OUT_FILE = os.path.join(HERE, "index.html")


def slide_key(filename):
    """Sort key: slide_15b_... comes between slide_15_... and slide_16_..."""
    base = os.path.basename(filename)
    m = re.match(r"slide_(\d+)([a-z]?)_", base)
    if not m:
        return (999, "")
    return (int(m.group(1)), m.group(2))


def extract_slide_div(content):
    """Pull the outer <div class='slide ...'>...</div> out of a full slide HTML file."""
    m = re.search(
        r'(<div class="slide[^"]*"[^>]*>.*</div>)\s*</body>',
        content,
        re.DOTALL,
    )
    return m.group(1) if m else None


def build():
    slide_files = sorted(glob.glob(os.path.join(SRC_DIR, "slide_*.html")), key=slide_key)
    if not slide_files:
        raise SystemExit(f"No slide files found in {SRC_DIR}")

    slides = []
    for f in slide_files:
        with open(f, "r") as fp:
            content = fp.read()
        slide_div = extract_slide_div(content)
        if not slide_div:
            print(f"WARN: could not extract slide div from {os.path.basename(f)}")
            continue
        slides.append((os.path.basename(f), slide_div))

    print(f"Combined {len(slides)} slides")

    total = len(slides)
    slide_divs = "\n\n".join(
        f'<div class="slide-wrapper" data-slide="{i+1}" data-filename="{fn}">\n{html}\n</div>'
        for i, (fn, html) in enumerate(slides)
    )

    template = TEMPLATE.replace("{{SLIDES}}", slide_divs).replace("{{TOTAL}}", str(total))

    with open(OUT_FILE, "w") as f:
        f.write(template)

    print(f"Wrote {OUT_FILE} ({os.path.getsize(OUT_FILE):,} bytes)")


# The template is loaded from the existing index.html if rebuild logic is
# extended; for now this script regenerates from a baked-in template.
TEMPLATE_PATH = os.path.join(HERE, "_template.html")
if os.path.exists(TEMPLATE_PATH):
    with open(TEMPLATE_PATH) as f:
        TEMPLATE = f.read()
else:
    # Inline default template — copy of the structure used to first generate index.html
    TEMPLATE = open(os.path.join(HERE, "index.html")).read() if os.path.exists(os.path.join(HERE, "index.html")) else ""
    # If index already exists, we replace its slide-wrappers block on rebuild
    if TEMPLATE:
        # Locate and strip existing slides
        TEMPLATE = re.sub(
            r'<div id="presentation">.*?</div>\s*\n\s*<!-- Overview',
            '<div id="presentation">\n{{SLIDES}}\n</div>\n\n<!-- Overview',
            TEMPLATE,
            count=1,
            flags=re.DOTALL,
        )
        # Update {{TOTAL}}
        TEMPLATE = re.sub(r'max="\d+"', 'max="{{TOTAL}}"', TEMPLATE)
        TEMPLATE = re.sub(r'/ \d+</span>', '/ {{TOTAL}}</span>', TEMPLATE)


if __name__ == "__main__":
    if not TEMPLATE:
        raise SystemExit("No template available. Run from a folder that already contains index.html, "
                         "or place a _template.html alongside this script.")
    build()
