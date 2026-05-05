"""Rendering helpers delegated to external :mod:`chatstyle`."""

from chatstyle import get_style, render_heading, render_note
from chatstyle.render.output import _get_console

_render_heading = render_heading
_render_note = render_note

__all__ = ["_get_console", "_render_heading", "_render_note", "get_style"]
