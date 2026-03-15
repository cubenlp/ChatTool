"""
XHS QR code capture utility.
"""
import os
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional, Sequence

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


def _crop_image(image_bytes: bytes, rect: dict) -> bytes:
    from PIL import Image

    img = Image.open(BytesIO(image_bytes))
    dpr = rect.get("dpr", 1)
    x = max(0, int(rect.get("x", 0) * dpr))
    y = max(0, int(rect.get("y", 0) * dpr))
    w = int(rect.get("width", 0) * dpr)
    h = int(rect.get("height", 0) * dpr)
    if w <= 0 or h <= 0:
        return image_bytes
    buf = BytesIO()
    img.crop((x, y, x + w, y + h)).save(buf, format="PNG")
    return buf.getvalue()


def _element_rect(client, selector: str) -> Optional[dict]:
    return client.eval(
        "(sel) => { const el = document.querySelector(sel); if (!el) return null;"
        " const r = el.getBoundingClientRect();"
        " return {x: r.left, y: r.top, width: r.width, height: r.height, dpr: window.devicePixelRatio || 1}; }",
        selector,
    )


def capture_xhs_qr(
    client,
    login_urls: Optional[Sequence[str]] = None,
    selectors: Optional[Sequence[str]] = None,
    timeout_ms: int = 15000,
    debug_dir: Optional[Path] = None,
) -> XhsQrCaptureResult:
    urls = list(login_urls or DEFAULT_XHS_LOGIN_URLS)
    sels = list(selectors or DEFAULT_QR_SELECTORS)

    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)

    for i, url in enumerate(urls):
        if not client.goto(url):
            continue

        print("[xhs] opened page")

        if debug_dir:
            (debug_dir / f"xhs_page_{i}.html").write_text(client.content(), encoding="utf-8", errors="ignore")
            data = client.screenshot(full_page=True)
            if data:
                (debug_dir / f"xhs_page_{i}.png").write_bytes(data)

        # find QR selector
        matched = None
        for sel in sels:
            if client.wait_for(sel, timeout=timeout_ms, state="visible"):
                matched = sel
                break
            if client.wait_for(sel, timeout=timeout_ms // 2, state="attached"):
                matched = sel
                break

        if matched:
            print(f"[xhs] selector matched: {matched}")
            rect = _element_rect(client, matched)
            data = client.screenshot(full_page=False)
            if rect and data:
                data = _crop_image(data, rect)
            if not data:
                raise XhsQrCaptureError("Failed to capture screenshot.")
            return XhsQrCaptureResult(url=url, selector=matched, image_bytes=data)

    # fallback: full screenshot of last page
    print("[xhs] no selector matched, fallback screenshot")
    data = client.screenshot(full_page=False)
    if not data:
        raise XhsQrCaptureError("Failed to capture fallback screenshot.")
    return XhsQrCaptureResult(url=urls[-1], selector=None, image_bytes=data)


def image_bytes_to_ascii(image_bytes: bytes, width: int = 64) -> str:
    try:
        from PIL import Image
    except ImportError as e:
        raise XhsQrCaptureError("Pillow is required for ASCII rendering.") from e

    img = Image.open(BytesIO(image_bytes)).convert("L")
    if img.width == 0 or img.height == 0:
        return ""
    h = max(1, int(width * img.height / img.width * 0.5))
    img = img.resize((width, h))
    return "\n".join(
        "".join("##" if img.getpixel((x, y)) < 128 else "  " for x in range(width))
        for y in range(h)
    )


def run_xhs_qr_capture(
    output_path: Optional[str] = None,
    timeout_ms: int = 15000,
    debug_enabled: bool = False,
    debug_dir: Optional[str] = None,
) -> XhsQrCaptureResult:
    from chattool.tools.browser import get_browser

    debug_path = None
    if debug_enabled or debug_dir:
        debug_path = Path(debug_dir or "/tmp/chattool_xhs_debug")

    with get_browser() as client:
        result = capture_xhs_qr(client, timeout_ms=timeout_ms, debug_dir=debug_path)

    if sys.stdout.isatty():
        ascii_art = image_bytes_to_ascii(result.image_bytes)
        if ascii_art:
            print(ascii_art)

    if output_path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(result.image_bytes)
        if sys.stdout.isatty():
            print(f"Saved: {output_path}")
    elif not sys.stdout.isatty():
        local = "/tmp/chattool_xhs_qr.png"
        Path(local).write_bytes(result.image_bytes)

    return result
