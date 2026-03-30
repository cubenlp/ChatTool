from __future__ import annotations

import sys
from dataclasses import dataclass
import os
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional, Sequence, TYPE_CHECKING
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

from chattool.config.browser import BrowserConfig

if TYPE_CHECKING:
    from chattool.tools.browser import BrowserClient


DEFAULT_XHS_LOGIN_URLS = [
    "https://www.xiaohongshu.com/login",
    "https://www.xiaohongshu.com/",
]

DEFAULT_QR_SELECTORS = [
    "img.qrcode-img",
    ".qrcode-img",
    ".qrcode-img-box img",
    ".qrcode-box img",
    "img[alt*='二维码']",
    "img[alt*='QR']",
    "img[src*='qr']",
    "img[src*='qrcode']",
    "canvas",
]


@dataclass(frozen=True)
class XhsQrCaptureResult:
    url: str
    selector: Optional[str]
    image_bytes: bytes


class XhsQrCaptureError(RuntimeError):
    pass


def normalize_backend(backend: Optional[str]) -> str:
    value = backend or BrowserConfig.BROWSER_DEFAULT_BACKEND.value or "playwright"
    value = str(value).strip().lower()
    if value not in {"selenium", "chromium", "playwright"}:
        raise XhsQrCaptureError(f"Unsupported backend: {value}")
    return value


def _require_value(value: Optional[str], name: str) -> str:
    if not value:
        raise XhsQrCaptureError(f"Missing config: {name}")
    return value


def _append_token(url: str, token: Optional[str]) -> str:
    if not token:
        return url
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if "token" in query:
        return url
    query["token"] = [token]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def create_client_for_backend(backend: Optional[str] = None) -> "BrowserClient":
    backend_value = normalize_backend(backend)
    if backend_value == "selenium":
        remote_url = _require_value(
            BrowserConfig.BROWSER_SELENIUM_REMOTE_URL.value,
            "BROWSER_SELENIUM_REMOTE_URL",
        )
        from chattool.tools.browser.selenium import SeleniumBrowserClient

        return SeleniumBrowserClient(
            remote_url=remote_url,
            browser="chrome",
            headless=True,
        )
    if backend_value == "chromium":
        cdp_url = _require_value(
            BrowserConfig.BROWSER_CHROMIUM_CDP_URL.value,
            "BROWSER_CHROMIUM_CDP_URL",
        )
        cdp_url = _append_token(cdp_url, BrowserConfig.BROWSER_CHROMIUM_TOKEN.value)
        try:
            from chattool.tools.browser.playwright_impl import PlaywrightBrowserClient
        except ImportError as exc:
            raise XhsQrCaptureError(str(exc)) from exc

        return PlaywrightBrowserClient(
            cdp_url=cdp_url,
            browser_type="chromium",
            headless=True,
        )
    if backend_value == "playwright":
        try:
            from chattool.tools.browser.playwright_impl import PlaywrightBrowserClient
        except ImportError as exc:
            raise XhsQrCaptureError(str(exc)) from exc

        return PlaywrightBrowserClient(
            cdp_url=None,
            browser_type="chromium",
            headless=True,
        )
    raise XhsQrCaptureError("Unknown backend.")


def _get_element_rect(client: "BrowserClient", selector: str) -> Optional[dict]:
    module = client.__class__.__module__
    if "selenium" in module:
        script = (
            "return (function(selector){"
            "const el = document.querySelector(selector);"
            "if (!el) return null;"
            "const r = el.getBoundingClientRect();"
            "return {x: r.left, y: r.top, width: r.width, height: r.height, dpr: (window.devicePixelRatio || 1)};"
            "})(arguments[0]);"
        )
        return client.execute_script(script, selector)

    script = (
        "(selector) => {"
        "const el = document.querySelector(selector);"
        "if (!el) return null;"
        "const r = el.getBoundingClientRect();"
        "return {x: r.left, y: r.top, width: r.width, height: r.height, dpr: (window.devicePixelRatio || 1)};"
        "}"
    )
    return client.execute_script(script, selector)


def _crop_image_bytes(image_bytes: bytes, rect: dict) -> bytes:
    from PIL import Image

    image = Image.open(BytesIO(image_bytes))
    x = max(0, int(rect.get("x", 0) * rect.get("dpr", 1)))
    y = max(0, int(rect.get("y", 0) * rect.get("dpr", 1)))
    width = int(rect.get("width", 0) * rect.get("dpr", 1))
    height = int(rect.get("height", 0) * rect.get("dpr", 1))

    if width <= 0 or height <= 0:
        return image_bytes

    cropped = image.crop((x, y, x + width, y + height))
    buffer = BytesIO()
    cropped.save(buffer, format="PNG")
    return buffer.getvalue()


def _select_first_selector(client: "BrowserClient", selectors: Iterable[str], timeout_ms: int) -> Optional[str]:
    for selector in selectors:
        if client.wait_for_selector(selector, timeout=timeout_ms, state="visible", quiet=True):
            return selector
        if client.wait_for_selector(selector, timeout=timeout_ms, state="attached", quiet=True):
            return selector
    return None


def capture_xhs_qr(
    client: "BrowserClient",
    login_urls: Optional[Sequence[str]] = None,
    selectors: Optional[Sequence[str]] = None,
    timeout_ms: int = 15000,
    debug_dir: Optional[Path] = None,
    verbose: bool = False,
) -> XhsQrCaptureResult:
    login_urls = list(login_urls or DEFAULT_XHS_LOGIN_URLS)
    selectors = list(selectors or DEFAULT_QR_SELECTORS)

    last_url = None
    last_error = None
    if not debug_dir:
        env_debug = os.getenv("XHS_DEBUG_DIR") or os.getenv("CHATTOOL_DEBUG_DIR")
        debug_dir = Path(env_debug).expanduser() if env_debug else None
    debug_path = debug_dir
    if debug_path:
        debug_path.mkdir(parents=True, exist_ok=True)
    for url in login_urls:
        last_url = url
        if not client.goto(url):
            last_error = f"Failed to navigate: {url}"
            continue
        try:
            title = client.get_title()
            current_url = client.get_url()
            if verbose:
                print(f"[xhs] opened: {current_url} | title: {title}")
            else:
                print("[xhs] opened page")
            if current_url and (
                "website-login/error" in current_url
                or "httpStatus=461" in current_url
                or "安全限制" in (title or "")
            ):
                raise XhsQrCaptureError("Blocked by XHS risk control (461).")
            if debug_path:
                html = client.get_page_content("html")
                (debug_path / f"xhs_page_{login_urls.index(url)}.html").write_text(
                    html, encoding="utf-8", errors="ignore"
                )
                image_bytes = client.screenshot(full_page=True)
                if image_bytes:
                    (debug_path / f"xhs_page_{login_urls.index(url)}.png").write_bytes(image_bytes)
        except Exception:
            pass
        selector = _select_first_selector(client, selectors, timeout_ms)
        if not selector:
            selector = _select_first_selector(client, selectors, timeout_ms // 2)
        if selector:
            if verbose:
                print(f"[xhs] selector matched: {selector}")
            else:
                print("[xhs] selector matched")
            rect = _get_element_rect(client, selector)
            image_bytes = client.screenshot(full_page=False)
            if rect and image_bytes:
                image_bytes = _crop_image_bytes(image_bytes, rect)
            if not image_bytes:
                raise XhsQrCaptureError("Failed to capture screenshot.")
            return XhsQrCaptureResult(url=url, selector=selector, image_bytes=image_bytes)

    if last_url:
        print("[xhs] no selector matched, fallback screenshot")
        image_bytes = client.screenshot(full_page=False)
        if not image_bytes:
            if last_error:
                raise XhsQrCaptureError(f"Failed to capture fallback screenshot. {last_error}")
            raise XhsQrCaptureError("Failed to capture fallback screenshot.")
        return XhsQrCaptureResult(url=last_url, selector=None, image_bytes=image_bytes)

    raise XhsQrCaptureError("No login URLs available.")


def image_bytes_to_ascii(image_bytes: bytes, width: int = 64) -> str:
    try:
        from PIL import Image
    except ImportError as exc:
        raise XhsQrCaptureError("Pillow is required for ASCII rendering.") from exc

    image = Image.open(BytesIO(image_bytes)).convert("L")
    if image.width == 0 or image.height == 0:
        return ""

    aspect_ratio = image.height / image.width
    target_height = max(1, int(width * aspect_ratio * 0.5))
    resized = image.resize((width, target_height))

    lines = []
    for y in range(resized.height):
        row_chars = []
        for x in range(resized.width):
            pixel = resized.getpixel((x, y))
            row_chars.append("##" if pixel < 128 else "  ")
        lines.append("".join(row_chars))
    return "\n".join(lines)


def _save_image(path: Path, image_bytes: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes)


def run_xhs_qr_capture(
    backend: Optional[str] = None,
    output_path: Optional[str] = None,
    timeout_ms: int = 15000,
    debug_enabled: bool = False,
    debug_dir: Optional[str] = None,
) -> XhsQrCaptureResult:
    def _execute():
        client = create_client_for_backend(backend)
        try:
            debug_path = None
            if debug_enabled or debug_dir:
                debug_path = Path(debug_dir or "/tmp/chattool_xhs_debug")
            result = capture_xhs_qr(
                client,
                timeout_ms=timeout_ms,
                debug_dir=debug_path,
                verbose=bool(debug_path),
            )

            if sys.stdout.isatty():
                ascii_art = image_bytes_to_ascii(result.image_bytes)
                if ascii_art:
                    print(ascii_art)
            else:
                if not output_path:
                    local_output = "/tmp/chattool_xhs_qr.png"
                else:
                    local_output = output_path
                _save_image(Path(local_output), result.image_bytes)
                return result

            if output_path:
                _save_image(Path(output_path), result.image_bytes)
                if sys.stdout.isatty():
                    print(f"Saved QR image: {output_path}")

            return result
        finally:
            try:
                client.close()
            except Exception:
                pass

    try:
        import asyncio
        asyncio.get_running_loop()
    except RuntimeError:
        return _execute()

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_execute)
        return future.result()
