#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert HTML legal documents (from net.jogtar.hu) to Markdown
"""

import html2text
import re
import sys
from pathlib import Path

def clean_legal_markdown(markdown_text, law_code, law_title):
    """Clean and format markdown for legal documents"""

    lines = markdown_text.split('\n')
    output = []

    # Add frontmatter
    output.append("---")
    output.append(f"title: {law_title}")
    output.append(f"law_code: {law_code}")
    output.append("source: net.jogtar.hu")
    output.append("last_checked: 2025-11-04")
    output.append("---")
    output.append("")

    skip_patterns = [
        "Hirdetés",
        "Bejelentkezés",
        "Regisztráció",
        "Cookie",
        "Wolters Kluwer",
        "Adatvédelmi",
        "ÁSZF",
        "Kapcsolat",
        "Facebook",
        "LinkedIn",
        "Copyright",
        "Feliratkozás",
        "Skip to",
        "[](http",  # Empty links
        "![](data:",  # Base64 images
    ]

    for line in lines:
        line = line.strip()

        # Skip empty lines (will be added back strategically)
        if not line:
            continue

        # Skip unwanted patterns
        if any(pattern in line for pattern in skip_patterns):
            continue

        # Skip pure markdown links with no text
        if re.match(r'^\[+\]+$', line):
            continue

        # Skip navigation/menu items
        if line.startswith('* [') and len(line) < 50:
            continue

        # Main title
        if law_title in line and line.startswith('#'):
            output.append(f"# {law_title}")
            output.append("")
            continue

        # Section headers (### becomes ##)
        if line.startswith('### '):
            section_title = line.replace('### ', '')
            # Check if it's an article (X. §, 1. §, etc.)
            if re.search(r'\d+\.\s*§', section_title):
                output.append(f"## {section_title}")
                output.append("")
                continue
            # Or section title
            output.append(f"## {section_title}")
            output.append("")
            continue

        # Level 2 headers (## becomes #)
        if line.startswith('## '):
            section_title = line.replace('## ', '')
            output.append(f"# {section_title}")
            output.append("")
            continue

        # Paragraph numbers (1), (2), etc. - make bold
        para_match = re.match(r'^(\(\d+\))\s*(.*)', line)
        if para_match:
            num = para_match.group(1)
            text = para_match.group(2)
            output.append(f"**{num}** {text}")
            output.append("")
            continue

        # Lists a), b), c) - format
        list_match = re.match(r'^([a-z])\)\s+(.*)', line)
        if list_match:
            letter = list_match.group(1)
            text = list_match.group(2)
            output.append(f"- **{letter})** {text}")
            continue

        # Regular text
        output.append(line)
        output.append("")

    return '\n'.join(output)


def convert_html_to_markdown(html_file, output_file=None, law_code="", law_title=""):
    """Convert HTML file to cleaned Markdown"""

    print(f"[1/4] Reading HTML file: {html_file}")

    # Read HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print(f"[2/4] Converting HTML to Markdown...")

    # Configure html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = False
    h.body_width = 0  # No line wrapping
    h.unicode_snob = True
    h.skip_internal_links = True

    # Convert
    markdown_raw = h.handle(html_content)

    print(f"[3/4] Cleaning and formatting...")

    # Clean and format
    markdown_clean = clean_legal_markdown(markdown_raw, law_code, law_title)

    # Determine output filename
    if not output_file:
        html_path = Path(html_file)
        output_file = html_path.stem + '.md'

    print(f"[4/4] Writing to: {output_file}")

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_clean)

    # Stats
    lines = len(markdown_clean.split('\n'))
    size_kb = len(markdown_clean.encode('utf-8')) / 1024

    print(f"\n[SUCCESS] Conversion complete!")
    print(f"  Lines: {lines}")
    print(f"  Size: {size_kb:.1f} KB")
    print(f"  Output: {output_file}")

    return output_file


if __name__ == "__main__":
    # BTK HTML file
    html_file = r"C:\Users\admin\Downloads\Btk. (új) - 2012. évi C. törvény a Büntető Törvénykönyvről - Hatályos Jogszabályok Gyűjteménye.html"
    output_file = "BTK.md"
    law_code = "2012. évi C. törvény"
    law_title = "Büntető Törvénykönyv"

    try:
        convert_html_to_markdown(html_file, output_file, law_code, law_title)
    except FileNotFoundError:
        print(f"\n[ERROR] HTML file not found: {html_file}")
        print("Please update the file path in the script.")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
