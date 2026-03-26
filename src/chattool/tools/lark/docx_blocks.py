from enum import IntEnum
from typing import Any, Dict, List, Optional


class DocxBlockType(IntEnum):
    PAGE = 1
    TEXT = 2
    HEADING1 = 3
    HEADING2 = 4
    HEADING3 = 5
    HEADING4 = 6
    HEADING5 = 7
    HEADING6 = 8
    HEADING7 = 9
    HEADING8 = 10
    HEADING9 = 11
    BULLET = 12
    ORDERED = 13
    CODE = 14
    QUOTE = 15
    TODO = 17
    CALLOUT = 19
    DIVIDER = 22


def make_text_elements(text: str) -> List[Dict[str, Any]]:
    return [{"text_run": {"content": text}}]


def make_text_block(text: str) -> Dict[str, Any]:
    return {
        "block_type": DocxBlockType.TEXT,
        "text": {"elements": make_text_elements(text)},
    }


def make_heading_block(text: str, level: int = 1) -> Dict[str, Any]:
    normalized_level = min(max(level, 1), 9)
    block_type = DocxBlockType.HEADING1 + normalized_level - 1
    heading_key = f"heading{normalized_level}"
    return {
        "block_type": block_type,
        heading_key: {"elements": make_text_elements(text)},
    }


def make_bullet_block(text: str) -> Dict[str, Any]:
    return {
        "block_type": DocxBlockType.BULLET,
        "bullet": {"elements": make_text_elements(text)},
    }


def make_ordered_block(text: str) -> Dict[str, Any]:
    return {
        "block_type": DocxBlockType.ORDERED,
        "ordered": {"elements": make_text_elements(text)},
    }


def make_code_block(text: str, language: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"elements": make_text_elements(text)}
    if language:
        payload["style"] = {"language": language}
    return {
        "block_type": DocxBlockType.CODE,
        "code": payload,
    }


def make_quote_block(text: str) -> Dict[str, Any]:
    return {
        "block_type": DocxBlockType.QUOTE,
        "quote": {"elements": make_text_elements(text)},
    }


def make_callout_block(text: str, emoji: Optional[str] = None, background_color: Optional[int] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"elements": make_text_elements(text)}
    if emoji or background_color is not None:
        payload["callout"] = {}
        if emoji:
            payload["callout"]["emoji_id"] = emoji
        if background_color is not None:
            payload["callout"]["background_color"] = background_color
    return {
        "block_type": DocxBlockType.CALLOUT,
        "callout": payload,
    }


def make_divider_block() -> Dict[str, Any]:
    return {
        "block_type": DocxBlockType.DIVIDER,
        "divider": {},
    }
