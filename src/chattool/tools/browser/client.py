"""
Browser client based on Playwright CDP.
Supports local launch and remote CDP connections.
"""
import logging
import time
from typing import Any, Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise ImportError(
        "Playwright is not installed. "
        "Run: pip install playwright && playwright install chromium"
    )

logger = logging.getLogger(__name__)


def _append_token(url: str, token: Optional[str]) -> str:
    if not token:
        return url
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if "token" not in query:
        query["token"] = [token]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


class BrowserClient:
    """Playwright-based browser client. Connects via CDP or launches locally."""

    def __init__(
        self,
        cdp_url: Optional[str] = None,
        headless: bool = True,
        timeout: int = 30000,
    ):
        self.cdp_url = cdp_url
        self.headless = headless
        self.timeout = timeout

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _ensure_started(self) -> None:
        if self._browser is not None:
            return
        self._playwright = sync_playwright().start()
        if self.cdp_url:
            logger.info(f"Connecting to remote CDP: {self.cdp_url}")
            self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
        else:
            logger.info(f"Launching local browser (headless={self.headless})")
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        self._page.set_default_timeout(self.timeout)

    @property
    def page(self):
        self._ensure_started()
        return self._page

    def goto(self, url: str) -> bool:
        try:
            self.page.goto(url)
            return True
        except Exception as e:
            logger.error(f"goto {url}: {e}")
            return False

    def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> Optional[bytes]:
        try:
            if path:
                self.page.screenshot(path=path, full_page=full_page)
                return None
            return self.page.screenshot(full_page=full_page)
        except Exception as e:
            logger.error(f"screenshot: {e}")
            return None

    def content(self) -> str:
        try:
            return self.page.content()
        except Exception as e:
            logger.error(f"content: {e}")
            return ""

    def text(self) -> str:
        try:
            return self.page.inner_text("body")
        except Exception as e:
            logger.error(f"text: {e}")
            return ""

    def eval(self, script: str, *args) -> Any:
        try:
            return self.page.evaluate(script, *args)
        except Exception as e:
            logger.error(f"eval: {e}")
            return None

    def cookies(self) -> list:
        try:
            return self.page.context.cookies()
        except Exception as e:
            logger.error(f"cookies: {e}")
            return []

    def click(self, selector: str) -> bool:
        try:
            self.page.click(selector)
            return True
        except Exception as e:
            logger.error(f"click {selector}: {e}")
            return False

    def wait_for(self, selector: str, timeout: Optional[int] = None, state: str = "visible") -> bool:
        deadline = time.monotonic() + (timeout or self.timeout) / 1000
        while time.monotonic() < deadline:
            handle = self.page.query_selector(selector)
            if handle:
                if state == "attached":
                    return True
                try:
                    visible = handle.is_visible()
                except Exception:
                    visible = True
                if state == "visible" and visible:
                    return True
                if state == "hidden" and not visible:
                    return True
            time.sleep(0.2)
        return False

    def title(self) -> str:
        try:
            return self.page.title()
        except Exception:
            return ""

    def url(self) -> str:
        try:
            return self.page.url
        except Exception:
            return ""

    def close(self) -> None:
        for attr in ("_page", "_context", "_browser", "_playwright"):
            obj = getattr(self, attr, None)
            if obj is not None:
                try:
                    obj.close() if attr != "_playwright" else obj.stop()
                except Exception:
                    pass
                setattr(self, attr, None)

    def __enter__(self):
        self._ensure_started()
        return self

    def __exit__(self, *args):
        self.close()
