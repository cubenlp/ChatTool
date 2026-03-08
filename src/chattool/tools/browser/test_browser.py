#!/usr/bin/env python3
"""
Browser 客户端测试脚本
用于验证连接到远程 CDP 浏览器
"""
import sys
import os
import logging

# 添加项目路径并避免导入 chattool 顶层
sys.path.insert(0, '/workspace/chattool/src')

# 直接导入 browser 模块，避免依赖问题
from chattool.tools.browser import create_browser_client


def setup_logging(level=logging.INFO):
    """设置日志"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_remote_browser(cdp_url: str = 'http://rexpc.oray.wzhecnu.cn:9222'):
    """测试远程浏览器连接"""
    logger = logging.getLogger(__name__)
    logger.info(f"Testing remote browser connection: {cdp_url}")
    
    # 创建 Playwright 客户端
    client = create_browser_client(
        browser_type='playwright',
        cdp_url=cdp_url,
        headless=True,
        timeout=30000,
        logger=logger
    )
    
    try:
        # 测试基础功能
        logger.info("Testing goto...")
        if not client.goto('https://www.baidu.com'):
            logger.error("Failed to navigate")
            return False
        
        logger.info(f"Current URL: {client.get_url()}")
        logger.info(f"Page title: {client.get_title()}")
        
        # 测试截图
        logger.info("Testing screenshot...")
        screenshot_path = '/workspace/test_screenshot.png'
        result = client.screenshot(path=screenshot_path, full_page=False)
        if result:
            logger.info(f"Screenshot saved to: {screenshot_path}")
        else:
            logger.warning("Screenshot returned None")
        
        # 测试获取页面内容
        logger.info("Testing get_page_content...")
        content = client.get_page_content(content_type='text')
        logger.info(f"Page content length: {len(content)}")
        
        # 测试执行脚本
        logger.info("Testing execute_script...")
        title = client.execute_script("document.title")
        logger.info(f"Title via script: {title}")
        
        # 测试 cookies
        logger.info("Testing get_cookies...")
        cookies = client.get_cookies()
        logger.info(f"Cookies count: {len(cookies)}")
        
        # 测试 localStorage
        logger.info("Testing get_local_storage...")
        storage = client.get_local_storage()
        logger.info(f"LocalStorage keys: {list(storage.keys())}")
        
        # 测试导航功能
        logger.info("Testing navigation...")
        client.goto('https://www.google.com')
        logger.info(f"After navigation - URL: {client.get_url()}")
        
        logger.info("Testing back...")
        client.back()
        logger.info(f"After back - URL: {client.get_url()}")
        
        logger.info("Testing forward...")
        client.forward()
        logger.info(f"After forward - URL: {client.get_url()}")
        
        logger.info("Testing refresh...")
        client.refresh()
        logger.info("Refresh completed")
        
        logger.info("✅ All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()
        logger.info("Browser closed")


def test_local_browser():
    """测试本地浏览器"""
    logger = logging.getLogger(__name__)
    logger.info("Testing local browser...")
    
    client = create_browser_client(
        browser_type='playwright',
        headless=True,
        logger=logger
    )
    
    try:
        client.goto('https://www.baidu.com')
        logger.info(f"URL: {client.get_url()}")
        logger.info(f"Title: {client.get_title()}")
        
        screenshot_path = '/workspace/test_local_screenshot.png'
        client.screenshot(path=screenshot_path)
        logger.info(f"Screenshot saved: {screenshot_path}")
        
        logger.info("✅ Local browser test passed!")
        return True
    except Exception as e:
        logger.error(f"Local test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


def test_selenium_browser(remote_url: str = None):
    """测试 Selenium"""
    logger = logging.getLogger(__name__)
    logger.info("Testing Selenium browser...")
    
    client = create_browser_client(
        browser_type='selenium',
        headless=True,
        remote_url=remote_url,
        browser='chrome',
        logger=logger
    )
    
    try:
        client.goto('https://www.baidu.com')
        logger.info(f"URL: {client.get_url()}")
        logger.info(f"Title: {client.get_title()}")
        
        logger.info("✅ Selenium test passed!")
        return True
    except Exception as e:
        logger.error(f"Selenium test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Browser Client Test')
    parser.add_argument('--cdp-url', type=str, default='http://rexpc.oray.wzhecnu.cn:9222',
                        help='CDP URL for remote browser')
    parser.add_argument('--remote-url', type=str, default=None,
                        help='Selenium remote URL')
    parser.add_argument('--local', action='store_true',
                        help='Test local browser instead of remote')
    parser.add_argument('--selenium', action='store_true',
                        help='Test Selenium instead of Playwright')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    args = parser.parse_args()
    
    setup_logging(logging.DEBUG if args.debug else logging.INFO)
    
    if args.local:
        test_local_browser()
    elif args.selenium:
        test_selenium_browser(remote_url=args.remote_url)
    else:
        test_remote_browser(cdp_url=args.cdp_url)
