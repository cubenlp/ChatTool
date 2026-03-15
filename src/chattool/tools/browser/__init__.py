"""
Browser tools - Playwright CDP client.
"""
from .client import BrowserClient, _append_token

from chattool.config.browser import BrowserConfig


def get_browser(
    cdp_url: str | None = None,
    headless: bool = True,
    timeout: int = 30000,
) -> BrowserClient:
    """Create a BrowserClient from args or environment config."""
    url = cdp_url or BrowserConfig.BROWSER_CHROMIUM_CDP_URL.value
    if url:
        url = _append_token(url, BrowserConfig.BROWSER_CHROMIUM_TOKEN.value)
    return BrowserClient(cdp_url=url, headless=headless, timeout=timeout)


__all__ = ["BrowserClient", "get_browser"]
