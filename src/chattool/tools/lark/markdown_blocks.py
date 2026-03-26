import re
from typing import List, Optional

from .docx_blocks import (
    make_bullet_block,
    make_code_block,
    make_divider_block,
    make_heading_block,
    make_ordered_block,
    make_quote_block,
    make_text_block,
)


_HEADING_RE = re.compile(r"^(#{1,9})\s+(.*)$")
_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_ORDERED_RE = re.compile(r"^\s*\d+\.\s+(.*)$")
_QUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
_DIVIDER_RE = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")
_FENCE_RE = re.compile(r"^\s*```([A-Za-z0-9_+-]*)\s*$")


def parse_markdown_blocks(markdown_text: str) -> List[dict]:
    """Convert a small, stable subset of Markdown into Feishu docx blocks."""
    blocks: List[dict] = []
    paragraph_lines: List[str] = []
    quote_lines: List[str] = []
    code_lines: List[str] = []
    code_language: Optional[str] = None

    def flush_paragraph() -> None:
        if paragraph_lines:
            text = " ".join(line.strip() for line in paragraph_lines if line.strip()).strip()
            if text:
                blocks.append(make_text_block(text))
            paragraph_lines.clear()

    def flush_quote() -> None:
        if quote_lines:
            text = "\n".join(line.rstrip() for line in quote_lines if line.strip()).strip()
            if text:
                blocks.append(make_quote_block(text))
            quote_lines.clear()

    def flush_code() -> None:
        nonlocal code_language
        if code_lines:
            blocks.append(make_code_block("\n".join(code_lines).rstrip(), language=code_language or None))
            code_lines.clear()
            code_language = None

    for raw_line in markdown_text.splitlines():
        fence_match = _FENCE_RE.match(raw_line)
        if fence_match:
            flush_paragraph()
            flush_quote()
            if code_lines:
                flush_code()
            else:
                code_language = fence_match.group(1) or None
            continue

        if code_lines or code_language is not None:
            code_lines.append(raw_line)
            continue

        stripped = raw_line.strip()
        if not stripped:
            flush_paragraph()
            flush_quote()
            continue

        heading_match = _HEADING_RE.match(stripped)
        if heading_match:
            flush_paragraph()
            flush_quote()
            blocks.append(make_heading_block(heading_match.group(2).strip(), level=len(heading_match.group(1))))
            continue

        if _DIVIDER_RE.match(stripped):
            flush_paragraph()
            flush_quote()
            blocks.append(make_divider_block())
            continue

        quote_match = _QUOTE_RE.match(raw_line)
        if quote_match:
            flush_paragraph()
            quote_lines.append(quote_match.group(1))
            continue
        flush_quote()

        bullet_match = _BULLET_RE.match(raw_line)
        if bullet_match:
            flush_paragraph()
            blocks.append(make_bullet_block(bullet_match.group(1).strip()))
            continue

        ordered_match = _ORDERED_RE.match(raw_line)
        if ordered_match:
            flush_paragraph()
            blocks.append(make_ordered_block(ordered_match.group(1).strip()))
            continue

        paragraph_lines.append(raw_line)

    flush_paragraph()
    flush_quote()
    flush_code()
    return blocks
