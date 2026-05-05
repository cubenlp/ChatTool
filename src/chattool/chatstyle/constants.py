"""Shared ChatTool CLI style constants."""

BACK_VALUE = "__BACK__"
CHECKBOX_SELECTED_INDICATOR = "[x]"
CHECKBOX_UNSELECTED_INDICATOR = "[ ]"
INTERACTIVE_OPTION_HELP = (
    "Auto prompt on missing args, -i forces interactive, -I disables it."
)
FORCE_INTERACTIVE_NO_TTY_MESSAGE = (
    "Interactive mode was requested, but no TTY is available in current terminal."
)
MISSING_REQUIRED_NO_TTY_MESSAGE = (
    "Missing required arguments and no TTY is available for interactive prompts."
)


__all__ = [
    "BACK_VALUE",
    "CHECKBOX_SELECTED_INDICATOR",
    "CHECKBOX_UNSELECTED_INDICATOR",
    "FORCE_INTERACTIVE_NO_TTY_MESSAGE",
    "INTERACTIVE_OPTION_HELP",
    "MISSING_REQUIRED_NO_TTY_MESSAGE",
]
