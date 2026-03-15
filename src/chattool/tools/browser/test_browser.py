#!/usr/bin/env python3
"""Browser client test script - validates remote CDP and local connections."""
import logging
import sys

from chattool.tools.browser import BrowserClient, get_browser


def setup_logging(debug=False):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def test_remote_browser(cdp_url: str):
    print(f"Testing remote browser: {cdp_url}")
    with BrowserClient(cdp_url=cdp_url) as client:
        client.goto("https://www.baidu.com")
        print(f"URL: {client.url()}")
        print(f"Title: {client.title()}")
        data = client.screenshot(full_page=False)
        print(f"Screenshot: {len(data)} bytes" if data else "Screenshot failed")
        text = client.text()
        print(f"Text length: {len(text)}")
        title = client.eval("document.title")
        print(f"Title via eval: {title}")
        cookies = client.cookies()
        print(f"Cookies: {len(cookies)}")
    print("✅ Remote browser test passed!")


def test_local_browser():
    print("Testing local browser...")
    with get_browser(headless=True) as client:
        client.goto("https://www.baidu.com")
        print(f"URL: {client.url()}")
        print(f"Title: {client.title()}")
    print("✅ Local browser test passed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--cdp-url", default=None)
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    setup_logging(args.debug)

    if args.local or not args.cdp_url:
        test_local_browser()
    else:
        test_remote_browser(args.cdp_url)
