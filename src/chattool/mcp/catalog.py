from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class MCPToolSpec:
    name: str
    module: str
    tags: Sequence[str]
    summary: str


TOOL_SPECS: Sequence[MCPToolSpec] = ()


def get_tool_specs() -> List[MCPToolSpec]:
    return list(TOOL_SPECS)


def get_visible_tool_specs(
    enable_tags: Iterable[str] | None = None,
    disable_tags: Iterable[str] | None = None,
) -> List[MCPToolSpec]:
    enabled = {t.strip() for t in (enable_tags or []) if t and t.strip()}
    disabled = {t.strip() for t in (disable_tags or []) if t and t.strip()}
    result = []
    for spec in TOOL_SPECS:
        tag_set = set(spec.tags)
        if enabled and not (tag_set & enabled):
            continue
        if disabled and (tag_set & disabled):
            continue
        result.append(spec)
    return result
