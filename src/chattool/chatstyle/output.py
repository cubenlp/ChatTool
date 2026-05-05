"""Compatibility rendering helpers delegated to external :mod:`chatstyle`."""

from chatstyle.render.output import _get_console
from chatstyle import get_style, render_heading, render_note

_render_heading = render_heading
_render_note = render_note
