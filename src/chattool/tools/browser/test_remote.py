#!/usr/bin/env python3
"""
Browser 客户端测试脚本 - 独立版本
用于验证连接到远程 CDP 浏览器。

这是手工 smoke script，不应阻塞自动化 pytest。
"""
from pathlib import Path
import sys
import logging

try:
    import pytest
except ImportError:  # pragma: no cover - script fallback
    pytest = None
else:
    if __name__ != "__main__":
        pytestmark = pytest.mark.skip(
            reason="Manual browser smoke script; excluded from automated pytest runs."
        )

REPO_ROOT = Path(__file__).resolve().parents[4]

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimplePlaywrightClient:
    """简化的 Playwright 客户端，用于测试"""
    
    def __init__(self, cdp_url: str = None, headless: bool = True):
        self.cdp_url = cdp_url
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._page = None
    
    def __enter__(self):
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        
        if self.cdp_url:
            logger.info(f"Connecting to remote browser: {self.cdp_url}")
            self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
        else:
            logger.info("Launching local browser")
            self._browser = self._playwright.chromium.launch(headless=self.headless)
        
        self._page = self._browser.new_page()
        return self
    
    def __exit__(self, *args):
        if self._page:
            self._page.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
    
    def goto(self, url: str) -> bool:
        try:
            self._page.goto(url, timeout=30000)
            return True
        except Exception as e:
            logger.error(f"Goto error: {e}")
            return False
    
    def get_url(self) -> str:
        return self._page.url
    
    def get_title(self) -> str:
        return self._page.title()
    
    def screenshot(self, path: str) -> bool:
        try:
            self._page.screenshot(path=path)
            return True
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return False
    
    def get_page_content(self) -> str:
        return self._page.content()
    
    def execute_script(self, script: str):
        return self._page.evaluate(script)
    
    def get_cookies(self):
        return self._page.context.cookies()
    
    def get_local_storage(self):
        return self._page.evaluate("""() => {
            const items = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                items[key] = localStorage.getItem(key);
            }
            return items;
        }""")


def test_remote_browser(cdp_url: str):
    """测试远程浏览器连接"""
    logger.info(f"Testing remote browser: {cdp_url}")
    
    with SimplePlaywrightClient(cdp_url=cdp_url, headless=True) as client:
        # 测试导航
        logger.info("Testing goto to baidu.com...")
        if not client.goto('https://www.baidu.com'):
            logger.error("Failed to navigate to baidu.com")
            return False
        
        logger.info(f"URL: {client.get_url()}")
        logger.info(f"Title: {client.get_title()}")
        
        # 测试截图
        logger.info("Testing screenshot...")
        screenshot_path = str(REPO_ROOT / 'test_remote_screenshot.png')
        if client.screenshot(screenshot_path):
            logger.info(f"Screenshot saved to {screenshot_path}")
        
        # 测试脚本执行
        logger.info("Testing execute_script...")
        title = client.execute_script("document.title")
        logger.info(f"Script result - title: {title}")
        
        # 测试 cookies
        logger.info("Testing get_cookies...")
        cookies = client.get_cookies()
        logger.info(f"Cookies count: {len(cookies)}")
        
        # 测试 localStorage
        logger.info("Testing get_local_storage...")
        storage = client.get_local_storage()
        logger.info(f"LocalStorage keys: {list(storage.keys())[:5]}...")
        
        # 测试其他网站
        logger.info("Testing navigation to google.com...")
        client.goto('https://www.google.com')
        logger.info(f"New URL: {client.get_url()}")
        
        logger.info("✅ All tests passed!")
        return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Browser Test')
    parser.add_argument('--cdp-url', type=str, default='http://rexpc.oray.wzhecnu.cn:9222',
                        help='CDP URL for remote browser')
    args = parser.parse_args()
    
    try:
        success = test_remote_browser(args.cdp_url)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
