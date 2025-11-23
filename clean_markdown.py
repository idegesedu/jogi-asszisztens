#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean and optimize Markdown files from HTML conversions
Removes JavaScript, navigation, ads, and other unwanted elements
"""

import re
import sys
from pathlib import Path

def clean_markdown_file(input_file, output_file=None, law_code="", law_title=""):
    """Clean markdown file from HTML conversion artifacts"""

    print(f"[1/4] Reading: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    print(f"[2/4] Cleaning... (original lines: {len(lines)})")

    # Patterns to skip (expanded list)
    skip_patterns = [
        # JavaScript and scripts
        'window.', 'adocf', 'AdOcean', 'ado.', 'gtm.js', 'googletagmanager',
        'dataLayer', 'Google Tag Manager',

        # HTML elements
        '<iframe', '</iframe>', '<script', '</script>',

        # Navigation
        'Ugrás az oldal', 'Hatályos Jogszabályok Gyűjteménye fejléc',
        'Új Jogtár bejelentkezés', 'Digital Compliance', 'Veszélyhelyzet',
        'Hatályos jogszabályok', 'Új jogszabályok', 'Módosított jogszabályok',
        'Önkormányzati rendelettár', 'Ezer év törvényei', 'Keresés',
        'Oldal nyomtatása', 'Vissza az oldal tetejére',

        # Images and links to assets
        '![', 'Kezdőlap', '/images/netjogtar',

        # Footer elements
        'Wolters Kluwer', 'Cégtörténet', 'Alapértékeink', 'ÁSZF',
        'Adatvédelmi', 'Cookie', 'Kapcsolat', 'Közösségi média',
        'Facebook', 'LinkedIn', 'Twitter', 'Instagram',

        # Copyright and legal notices from website
        'Copyright ©', '© 20',

        # Breadcrumbs - patterns like "1. [Link]", "2. [Link]"
        # (but NOT paragraph numbers like "(1)")
    ]

    output = []

    # Add frontmatter if provided
    if law_title and law_code:
        output.append("---")
        output.append(f"title: {law_title}")
        output.append(f"law_code: {law_code}")
        output.append("source: net.jogtar.hu")
        output.append("last_checked: 2025-11-04")
        output.append("---")
        output.append("")

    skip_until_content = True
    content_started = False
    in_footer = False

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Skip empty lines at the start
        if skip_until_content and not line_stripped:
            continue

        # Check if we hit actual content (first real heading or paragraph)
        if not content_started:
            # Look for year pattern like "2013. évi V. törvény"
            if re.search(r'\d{4}\.\s*évi\s+[IVXLC]+\.?\s+törvény', line_stripped):
                content_started = True
                skip_until_content = False
            # Or major section titles in all caps
            elif line_stripped.isupper() and len(line_stripped) > 10:
                content_started = True
                skip_until_content = False
            # Or numbered sections like "1. §"
            elif re.match(r'^\d+\.\s*§', line_stripped):
                content_started = True
                skip_until_content = False

        # Skip lines before content starts
        if skip_until_content:
            continue

        # Detect footer section
        if any(pattern in line for pattern in ['Beiktatta:', 'Módosította:', 'Hatályon kívül helyezte:', 'Megállapította:']):
            in_footer = True

        # Skip footer lines
        if in_footer:
            continue

        # Skip lines with unwanted patterns
        if any(pattern in line for pattern in skip_patterns):
            continue

        # Skip breadcrumb-style navigation (but not paragraph numbers)
        if re.match(r'^\d+\.\s+\[', line_stripped) and len(line_stripped) < 100:
            continue

        # Skip horizontal rules at the start of content
        if line_stripped == '---' and len(output) < 20:
            continue

        # Skip lines that are just links
        if re.match(r'^\[.*\]\(.*\)$', line_stripped) and len(line_stripped) < 100:
            continue

        # Skip asterisk markers  lines
        if line_stripped == '* * *':
            continue

        # Add the line
        output.append(line)

    print(f"[3/4] Formatting... (cleaned lines: {len(output)})")

    # Post-processing: remove excessive blank lines
    final_output = []
    prev_blank = False

    for line in output:
        is_blank = not line.strip()

        # Skip consecutive blank lines
        if is_blank and prev_blank:
            continue

        final_output.append(line)
        prev_blank = is_blank

    # Determine output filename
    if not output_file:
        input_path = Path(input_file)
        output_file = input_path.stem + '_clean.md'

    print(f"[4/4] Writing to: {output_file}")

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_output))

    # Stats
    original_lines = len(lines)
    cleaned_lines = len(final_output)
    reduction = ((original_lines - cleaned_lines) / original_lines * 100) if original_lines > 0 else 0
    size_kb = len('\n'.join(final_output).encode('utf-8')) / 1024

    print(f"\n[SUCCESS] Cleaning complete!")
    print(f"  Original lines: {original_lines}")
    print(f"  Cleaned lines: {cleaned_lines}")
    print(f"  Reduction: {reduction:.1f}%")
    print(f"  Size: {size_kb:.1f} KB")
    print(f"  Output: {output_file}")

    return output_file


# Law metadata
LAWS = {
    "Ptk. (új) - 2013. évi V.md": {
        "law_code": "2013. évi V. törvény",
        "law_title": "Polgári Törvénykönyv",
        "output": "Ptk_clean.md"
    },
    "Be. (új) - 2017. évi XC.md": {
        "law_code": "2017. évi XC. törvény",
        "law_title": "Büntetőeljárási törvény",
        "output": "Be_clean.md"
    },
    "Rtv. - 1994. évi XXXIV.md": {
        "law_code": "1994. évi XXXIV. törvény",
        "law_title": "Rendőrségi törvény",
        "output": "Rtv_clean.md"
    },
    "Fgy. tv. - 1997. évi CLV.md": {
        "law_code": "1997. évi CLV. törvény",
        "law_title": "Fogyasztóvédelmi törvény",
        "output": "Fgy_tv_clean.md"
    },
    "BTK.md": {
        "law_code": "2012. évi C. törvény",
        "law_title": "Büntető Törvénykönyv",
        "output": "BTK_clean.md"
    }
}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single file mode
        input_file = sys.argv[1]
        clean_markdown_file(input_file)
    else:
        # Batch mode - clean all laws
        print("=" * 60)
        print("BATCH CLEANING MODE - Processing all laws...")
        print("=" * 60)

        for law_file, metadata in LAWS.items():
            if Path(law_file).exists():
                print(f"\n{'='*60}")
                try:
                    clean_markdown_file(
                        law_file,
                        metadata["output"],
                        metadata["law_code"],
                        metadata["law_title"]
                    )
                except Exception as e:
                    print(f"[ERROR] Failed to process {law_file}: {e}")
            else:
                print(f"\n[SKIP] {law_file} - file not found")

        print(f"\n{'='*60}")
        print("[DONE] Batch cleaning complete!")
        print("=" * 60)
