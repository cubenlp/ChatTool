"""Shared warning filters for ChatTool CLI entrypoints."""

from __future__ import annotations

import warnings


def install_cli_warning_filters() -> None:
    """Hide noisy third-party warnings that do not affect CLI behavior."""
    warnings.filterwarnings(
        "ignore",
        message="pkg_resources is deprecated as an API.*",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=r"Deprecated call to `pkg_resources\.declare_namespace.*",
        category=DeprecationWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="There is no current event loop",
        category=DeprecationWarning,
    )
