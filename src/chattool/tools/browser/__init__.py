"""
Browser 自动化工具包
支持 Playwright 和 Selenium 两种实现
"""
import logging
from enum import Enum
from typing import Union, Optional, Dict, Any

from .base import BrowserClient
from .playwright_impl import PlaywrightBrowserClient, AsyncPlaywrightBrowserClient
from .selenium import SeleniumBrowserClient


class BrowserType(Enum):
    """支持的浏览器类型"""
    PLAYWRIGHT = 'playwright'
    SELENIUM = 'selenium'
    PLAYWRIGHT_ASYNC = 'playwright_async'


def create_browser_client(
    browser_type: Union[BrowserType, str] = 'playwright',
    cdp_url: Optional[str] = None,
    remote_url: Optional[str] = None,
    headless: bool = True,
    timeout: int = 30000,
    browser: str = 'chrome',
    browser_type_launcher: str = 'chromium',
    viewport: Optional[Dict[str, int]] = None,
    user_agent: Optional[str] = None,
    driver_path: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> BrowserClient:
    """
    创建浏览器客户端工厂函数
    
    Args:
        browser_type: 浏览器类型 ('playwright', 'selenium', 'playwright_async')
        cdp_url: Playwright 远程 CDP 地址 (如 'http://rexpc.oray.wzhecnu.cn:9222')
        remote_url: Selenium 远程 WebDriver 地址
        headless: 是否使用无头模式
        timeout: 默认超时时间（毫秒）
        browser: Selenium 浏览器类型 ('chrome', 'firefox', 'edge')
        browser_type_launcher: Playwright 浏览器启动器 ('chromium', 'firefox', 'webkit')
        viewport: 视口大小
        user_agent: 用户代理
        driver_path: WebDriver 路径
        logger: 日志记录器
        **kwargs: 其他参数
        
    Returns:
        BrowserClient 实例
        
    Example:
        # 使用 Playwright 连接远程 CDP
        client = create_browser_client(
            browser_type='playwright',
            cdp_url='http://rexpc.oray.wzhecnu.cn:9222'
        )
        
        # 使用 Playwright 本地
        client = create_browser_client(browser_type='playwright', headless=False)
        
        # 使用 Selenium
        client = create_browser_client(browser_type='selenium', browser='chrome')
    """
    if isinstance(browser_type, BrowserType):
        browser_type = browser_type.value
    
    if browser_type == 'playwright':
        return PlaywrightBrowserClient(
            logger=logger,
            headless=headless,
            timeout=timeout,
            browser_type=browser_type_launcher,
            cdp_url=cdp_url,
            viewport=viewport,
            user_agent=user_agent,
            **kwargs
        )
    elif browser_type == 'playwright_async':
        return AsyncPlaywrightBrowserClient(
            logger=logger,
            headless=headless,
            timeout=timeout,
            browser_type=browser_type_launcher,
            cdp_url=cdp_url,
            viewport=viewport,
            user_agent=user_agent,
            **kwargs
        )
    elif browser_type == 'selenium':
        return SeleniumBrowserClient(
            logger=logger,
            headless=headless,
            timeout=timeout,
            browser=browser,
            driver_path=driver_path,
            remote_url=remote_url,
            **kwargs
        )
    else:
        raise ValueError(f"Unsupported browser type: {browser_type}")


# 便捷函数
def create_remote_browser_client(
    cdp_url: str,
    browser_type: str = 'playwright',
    headless: bool = True,
    timeout: int = 30000,
    logger: Optional[logging.Logger] = None
) -> BrowserClient:
    """
    创建连接到远程浏览器的客户端
    
    Args:
        cdp_url: 远程 CDP 地址
        browser_type: 浏览器类型
        headless: 是否使用无头模式
        timeout: 超时时间
        logger: 日志记录器
        
    Returns:
        BrowserClient 实例
    """
    return create_browser_client(
        browser_type=browser_type,
        cdp_url=cdp_url,
        headless=headless,
        timeout=timeout,
        logger=logger
    )


__all__ = [
    'BrowserClient',
    'BrowserType',
    'PlaywrightBrowserClient',
    'AsyncPlaywrightBrowserClient',
    'SeleniumBrowserClient',
    'create_browser_client',
    'create_remote_browser_client',
]
