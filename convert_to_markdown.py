#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert alaptörvény.docx to proper Markdown format
"""

import re
from docx import Document

def convert_to_markdown(docx_path, output_path):
    """Convert Word document to Markdown with proper formatting"""

    print(f"Reading {docx_path}...")
    doc = Document(docx_path)

    # Output lines
    output = []

    # Add frontmatter
    output.append("---")
    output.append("title: Magyarország Alaptörvénye")
    output.append("effective_date: 2011-04-25")
    output.append("source: net.jogtar.hu")
    output.append("last_checked: 2025-11-04")
    output.append("---")
    output.append("")

    skip_patterns = [
        "Hirdetés",
        "A jogszabály mai napon",
        "jelek a bekezdések múltbeli"
    ]

    previous_was_section = False

    for para in doc.paragraphs:
        text = para.text.strip()

        # Skip empty lines and junk
        if not text:
            continue

        # Skip unwanted lines
        if any(pattern in text for pattern in skip_patterns):
            continue

        # Main title
        if "Magyarország Alaptörvénye" in text and "(2011" in text:
            output.append(f"# {text}")
            output.append("")
            continue

        # Date line
        if re.match(r'^\(20\d\d\.\s+\w+\s+\d+\.\)$', text):
            output.append(f"*{text}*")
            output.append("")
            continue

        # "Isten, áldd meg a magyart!" - blockquote
        if "Isten, áldd meg" in text:
            output.append(f"> {text}")
            output.append("")
            continue

        # Major sections (ALL CAPS, longer than 5 chars, not starting with parenthesis)
        if (text.isupper() and
            len(text) > 5 and
            not text.startswith('(') and
            not re.match(r'^[A-Z]\)\s+cikk', text) and
            not text.startswith('MI,')):

            if previous_was_section:
                output.append("")
            output.append("---")
            output.append("")
            output.append(f"# {text}")
            output.append("")
            previous_was_section = True
            continue

        # Article headers - letter style (A) cikk, B) cikk, etc.)
        article_match = re.match(r'^([A-Z])\)\s+cikk', text)
        if article_match:
            output.append(f"## {text}")
            output.append("")
            previous_was_section = False
            continue

        # Article headers - Roman numerals (I. cikk, II. cikk, etc.)
        roman_match = re.match(r'^([IVX]+)\.\s+cikk', text)
        if roman_match:
            output.append(f"## {text}")
            output.append("")
            previous_was_section = False
            continue

        # Numbered article headers (1. cikk, 2. cikk, etc.)
        numbered_article_match = re.match(r'^(\d+)\.\s+cikk', text)
        if numbered_article_match:
            output.append(f"## {text}")
            output.append("")
            previous_was_section = False
            continue

        # Paragraphs starting with (1), (2), etc.
        para_match = re.match(r'^\((\d+)\)\s+(.*)', text)
        if para_match:
            num = para_match.group(1)
            rest = para_match.group(2)
            output.append(f"**({num})** {rest}")
            output.append("")
            previous_was_section = False
            continue

        # Section titles ending with asterisk (like "NEMZETI HITVALLÁS *")
        if text.isupper() and text.endswith('*'):
            output.append("---")
            output.append("")
            output.append(f"# {text.rstrip('* ')}")
            output.append("")
            previous_was_section = True
            continue

        # Lists starting with a), b), c)
        list_match = re.match(r'^([a-z])\)\s+(.*)', text)
        if list_match:
            letter = list_match.group(1)
            rest = list_match.group(2)
            output.append(f"- **{letter})** {rest}")
            previous_was_section = False
            continue

        # Regular text
        output.append(text)
        output.append("")
        previous_was_section = False

    # Write to file
    print(f"Writing to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    print(f"[OK] Conversion complete!")
    print(f"   Lines written: {len(output)}")
    print(f"   Output file: {output_path}")

    return len(output)

if __name__ == "__main__":
    input_file = "alaptörvény.docx"
    output_file = "alaptörvény.md"

    try:
        line_count = convert_to_markdown(input_file, output_file)
        print(f"\n[SUCCESS] Created {output_file} with {line_count} lines")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
