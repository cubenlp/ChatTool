import pytest

from chattool.config.browser import BrowserConfig
from chattool.tools.browser import xhs_qrcode


def test_normalize_backend_default():
    BrowserConfig.BROWSER_DEFAULT_BACKEND.value = "playwright"
    assert xhs_qrcode.normalize_backend(None) == "playwright"


def test_normalize_backend_invalid():
    with pytest.raises(xhs_qrcode.XhsQrCaptureError):
        xhs_qrcode.normalize_backend("unknown")


def test_default_login_urls_present():
    assert xhs_qrcode.DEFAULT_XHS_LOGIN_URLS


def test_default_qr_selectors_present():
    assert xhs_qrcode.DEFAULT_QR_SELECTORS


def test_image_bytes_to_ascii_smoke():
    pil = pytest.importorskip("PIL")
    from PIL import Image
    from io import BytesIO

    image = Image.new("L", (10, 10), color=0)
    buf = BytesIO()
    image.save(buf, format="PNG")
    ascii_art = xhs_qrcode.image_bytes_to_ascii(buf.getvalue(), width=10)
    assert ascii_art.strip() != ""


def test_create_client_requires_urls():
    BrowserConfig.BROWSER_DEFAULT_BACKEND.value = "selenium"
    BrowserConfig.BROWSER_SELENIUM_REMOTE_URL.value = None
    with pytest.raises(xhs_qrcode.XhsQrCaptureError):
        xhs_qrcode.create_client_for_backend()
