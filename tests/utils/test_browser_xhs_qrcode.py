import pytest

from chattool.tools.browser import xhs_qrcode


def test_default_login_urls_present():
    assert xhs_qrcode.DEFAULT_XHS_LOGIN_URLS


def test_default_qr_selectors_present():
    assert xhs_qrcode.DEFAULT_QR_SELECTORS


def test_image_bytes_to_ascii_smoke():
    pytest.importorskip("PIL")
    from PIL import Image
    from io import BytesIO

    image = Image.new("L", (10, 10), color=0)
    buf = BytesIO()
    image.save(buf, format="PNG")
    ascii_art = xhs_qrcode.image_bytes_to_ascii(buf.getvalue(), width=10)
    assert ascii_art.strip() != ""
