"""Compatibility mask helpers delegated to external :mod:`chatstyle`."""

from chatstyle import format_current_secret, mask_secret, prompt_sensitive_value


__all__ = ["format_current_secret", "mask_secret", "prompt_sensitive_value"]
