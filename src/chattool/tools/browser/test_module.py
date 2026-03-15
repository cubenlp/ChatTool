#!/usr/bin/env python3
"""Browser module structure test."""
import sys
sys.path.insert(0, '/home/zhihong/workspace/ChatTool/src')

from chattool.tools.browser import BrowserClient, get_browser


def test_module_structure():
    print("Testing module structure...")
    assert BrowserClient is not None, "BrowserClient not found"
    assert get_browser is not None, "get_browser not found"
    print("✓ BrowserClient and get_browser exported")

    # Check key methods exist
    for method in ("goto", "screenshot", "content", "eval", "cookies", "click", "wait_for", "close"):
        assert hasattr(BrowserClient, method), f"Method {method} not found"
    print(f"✓ All required methods present")


def test_client_creation():
    print("Testing client creation...")
    client = BrowserClient(headless=True)
    assert client.cdp_url is None
    assert client.headless is True
    print("✓ Local client created (not started)")

    client = BrowserClient(cdp_url="http://localhost:9222")
    assert client.cdp_url == "http://localhost:9222"
    print("✓ Remote client created (not started)")

    client = get_browser()
    assert isinstance(client, BrowserClient)
    print("✓ get_browser() works")


if __name__ == "__main__":
    test_module_structure()
    test_client_creation()
    print("\n✅ ALL TESTS PASSED!")
