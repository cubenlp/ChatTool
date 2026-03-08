"""
Playwright 浏览器客户端实现
支持本地和远程 CDP 连接
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any, Union
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    from playwright.async_api import async_playwright
except ImportError:
    raise ImportError(
        "Playwright is not installed. "
        "Install it with: pip install playwright && playwright install chromium"
    )

from .base import BrowserClient


class PlaywrightBrowserClient(BrowserClient):
    """Playwright 浏览器客户端"""
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        headless: bool = True,
        timeout: int = 30000,
        # Playwright 特定参数
        browser_type: str = 'chromium',  # chromium, firefox, webkit
        cdp_url: Optional[str] = None,    # 远程 CDP 地址
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ):
        """
        初始化 Playwright 浏览器客户端
        
        Args:
            logger: 日志记录器
            headless: 是否使用无头模式
            timeout: 默认超时时间
            browser_type: 浏览器类型
            cdp_url: 远程 CDP 地址 (如 'http://rexpc.oray.wzhecnu.cn:9222')
            viewport: 视口大小
            user_agent: 用户代理
        """
        super().__init__(logger=logger, headless=headless, timeout=timeout, **kwargs)
        
        self.browser_type = browser_type
        self.cdp_url = cdp_url
        self.viewport = viewport or {'width': 1280, 'height': 720}
        self.user_agent = user_agent
        
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        
    def _ensure_browser(self) -> None:
        """确保浏览器已启动"""
        if self._browser is None:
            self._init_browser()
    
    def _init_browser(self) -> None:
        """初始化浏览器"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright is not installed. "
                "Install it with: pip install playwright && playwright install chromium"
            )
        
        self._playwright = sync_playwright().start()
        
        # 根据是否提供 CDP URL 决定连接方式
        if self.cdp_url:
            self.logger.info(f"Connecting to remote browser via CDP: {self.cdp_url}")
            # 连接到远程浏览器
            self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
        else:
            # 启动本地浏览器
            self.logger.info(f"Launching local {self.browser_type} browser (headless={self.headless})")
            browser_launcher = getattr(self._playwright, self.browser_type)
            self._browser = browser_launcher.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
        
        # 创建上下文
        context_options = {
            'viewport': self.viewport,
        }
        if self.user_agent:
            context_options['user_agent'] = self.user_agent
            
        self._context = self._browser.new_context(**context_options)
        
        # 创建页面
        self._page = self._context.new_page()
        
        # 设置默认超时
        self._page.set_default_timeout(self.timeout)
        
        self.logger.info("Browser initialized successfully")
    
    def _get_page(self):
        """获取当前页面"""
        self._ensure_browser()
        return self._page

    # ==================== 基础接口实现 ====================
    
    def goto(self, url: str, timeout: Optional[int] = None, **kwargs) -> bool:
        """导航到指定 URL"""
        try:
            page = self._get_page()
            timeout_ms = timeout or self.timeout
            self.logger.info(f"Navigating to: {url}")
            
            response = page.goto(url, timeout=timeout_ms, **kwargs)
            
            if response:
                self.logger.info(f"Page loaded with status: {response.status}")
                return True
            return True  # 有时 response 为 None 但页面仍加载成功
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {e}")
            return False

    def back(self) -> bool:
        """后退"""
        try:
            page = self._get_page()
            page.go_back()
            return True
        except Exception as e:
            self.logger.error(f"Go back error: {e}")
            return False

    def forward(self) -> bool:
        """前进"""
        try:
            page = self._get_page()
            page.go_forward()
            return True
        except Exception as e:
            self.logger.error(f"Go forward error: {e}")
            return False

    def refresh(self) -> bool:
        """刷新"""
        try:
            page = self._get_page()
            page.reload()
            return True
        except Exception as e:
            self.logger.error(f"Refresh error: {e}")
            return False

    def screenshot(self, path: Optional[str] = None, full_page: bool = False, **kwargs) -> Optional[bytes]:
        """截图"""
        try:
            page = self._get_page()
            
            options = {'full_page': full_page, **kwargs}
            
            if path:
                page.screenshot(path=path, **options)
                self.logger.info(f"Screenshot saved to: {path}")
                return path.encode() if path else None
            else:
                data = page.screenshot(**options)
                return data
        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            return None

    def get_page_content(self, content_type: str = 'html') -> str:
        """获取页面内容"""
        try:
            page = self._get_page()
            
            if content_type == 'html':
                return page.content()
            elif content_type == 'text':
                return page.inner_text('body')
            else:
                self.logger.warning(f"Unknown content type: {content_type}")
                return ""
        except Exception as e:
            self.logger.error(f"Get page content error: {e}")
            return ""

    def click(self, selector: str, timeout: Optional[int] = None, **kwargs) -> bool:
        """点击元素"""
        try:
            page = self._get_page()
            timeout_ms = timeout or self.timeout
            
            page.click(selector, timeout=timeout_ms, **kwargs)
            self.logger.debug(f"Clicked: {selector}")
            return True
        except Exception as e:
            self.logger.error(f"Click error ({selector}): {e}")
            return False

    def type(self, selector: str, text: str, delay: int = 0, timeout: Optional[int] = None, **kwargs) -> bool:
        """输入文本"""
        try:
            page = self._get_page()
            timeout_ms = timeout or self.timeout
            
            # 先清空输入框
            page.fill(selector, '', timeout=timeout_ms)
            # 输入文本
            page.type(selector, text, delay=delay, timeout=timeout_ms, **kwargs)
            self.logger.debug(f"Typed to: {selector}")
            return True
        except Exception as e:
            self.logger.error(f"Type error ({selector}): {e}")
            return False

    def hover(self, selector: str, timeout: Optional[int] = None, **kwargs) -> bool:
        """悬停"""
        try:
            page = self._get_page()
            timeout_ms = timeout or self.timeout
            
            page.hover(selector, timeout=timeout_ms, **kwargs)
            self.logger.debug(f"Hovered: {selector}")
            return True
        except Exception as e:
            self.logger.error(f"Hover error ({selector}): {e}")
            return False

    def wait_for_selector(self, selector: str, timeout: Optional[int] = None, state: str = 'visible', **kwargs) -> bool:
        """等待元素"""
        try:
            page = self._get_page()
            timeout_ms = timeout or self.timeout
            
            page.wait_for_selector(selector, timeout=timeout_ms, state=state, **kwargs)
            self.logger.debug(f"Element found: {selector}")
            return True
        except Exception as e:
            self.logger.error(f"Wait for selector error ({selector}): {e}")
            return False

    def execute_script(self, script: str, *args) -> Any:
        """执行 JavaScript"""
        try:
            page = self._get_page()
            return page.evaluate(script, *args)
        except Exception as e:
            self.logger.error(f"Execute script error: {e}")
            return None

    # ==================== 高级接口实现 ====================
    
    def get_cookies(self) -> List[Dict[str, Any]]:
        """获取 cookies"""
        try:
            page = self._get_page()
            return page.context.cookies()
        except Exception as e:
            self.logger.error(f"Get cookies error: {e}")
            return []

    def set_cookie(self, cookie: Dict[str, Any]) -> bool:
        """设置 cookie"""
        try:
            page = self._get_page()
            page.context.add_cookies([cookie])
            self.logger.debug(f"Cookie set: {cookie.get('name')}")
            return True
        except Exception as e:
            self.logger.error(f"Set cookie error: {e}")
            return False

    def delete_cookie(self, name: str, **kwargs) -> bool:
        """删除 cookie"""
        try:
            page = self._get_page()
            page.context.clear_cookies()
            # 如果只需要删除特定 cookie，需要先获取再过滤
            self.logger.debug(f"Cookies cleared")
            return True
        except Exception as e:
            self.logger.error(f"Delete cookie error: {e}")
            return False

    def get_local_storage(self) -> Dict[str, str]:
        """获取 localStorage"""
        try:
            page = self._get_page()
            return page.evaluate("""() => {
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            }""")
        except Exception as e:
            self.logger.error(f"Get localStorage error: {e}")
            return {}

    def set_local_storage(self, key: str, value: str) -> bool:
        """设置 localStorage"""
        try:
            page = self._get_page()
            page.evaluate(f"""(key, value) => {{
                localStorage.setItem(key, value);
            }}""", key, value)
            self.logger.debug(f"localStorage set: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Set localStorage error: {e}")
            return False

    def press_key(self, key: str, **kwargs) -> bool:
        """模拟按键"""
        try:
            page = self._get_page()
            page.keyboard.press(key, **kwargs)
            self.logger.debug(f"Key pressed: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Press key error: {e}")
            return False

    # ==================== 生命周期管理 ====================
    
    def close(self) -> None:
        """关闭浏览器"""
        try:
            if self._page:
                self._page.close()
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            
            self.logger.info("Browser closed")
        except Exception as e:
            self.logger.error(f"Close browser error: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        self._ensure_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False


class AsyncPlaywrightBrowserClient(BrowserClient):
    """异步 Playwright 浏览器客户端"""
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        headless: bool = True,
        timeout: int = 30000,
        browser_type: str = 'chromium',
        cdp_url: Optional[str] = None,
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ):
        super().__init__(logger=logger, headless=headless, timeout=timeout, **kwargs)
        
        self.browser_type = browser_type
        self.cdp_url = cdp_url
        self.viewport = viewport or {'width': 1280, 'height': 720}
        self.user_agent = user_agent
        
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
    
    def _ensure_browser(self):
        if self._browser is None:
            self._init_browser()
    
    def _init_browser(self):
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright is not installed. "
                "Install it with: pip install playwright && playwright install chromium"
            )
        
        self._playwright = asyncio.run(async_playwright().start())
        
        if self.cdp_url:
            self.logger.info(f"Connecting to remote browser via CDP: {self.cdp_url}")
            self._browser = asyncio.run(
                self._playwright.chromium.connect_over_cdp(self.cdp_url)
            )
        else:
            self.logger.info(f"Launching local {self.browser_type} browser")
            browser_launcher = getattr(self._playwright, self.browser_type)
            self._browser = asyncio.run(
                browser_launcher.launch(
                    headless=self.headless,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
            )
        
        context_options = {'viewport': self.viewport}
        if self.user_agent:
            context_options['user_agent'] = self.user_agent
            
        self._context = asyncio.run(self._browser.new_context(**context_options))
        self._page = asyncio.run(self._context.new_page())
        self._page.set_default_timeout(self.timeout)
        
        self.logger.info("Async browser initialized")
    
    def _get_page(self):
        self._ensure_browser()
        return self._page

    async def _run_async(self, coro):
        """运行异步协程"""
        return asyncio.run(coro)

    # 基础接口 - 这里提供简化实现，完整实现类似同步版本
    def goto(self, url: str, timeout: Optional[int] = None, **kwargs) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.goto(url, timeout=timeout or self.timeout))
            return True
        except Exception as e:
            self.logger.error(f"Goto error: {e}")
            return False

    def back(self) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.go_back())
            return True
        except Exception as e:
            return False

    def forward(self) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.go_forward())
            return True
        except Exception as e:
            return False

    def refresh(self) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.reload())
            return True
        except Exception as e:
            return False

    def screenshot(self, path: Optional[str] = None, full_page: bool = False, **kwargs) -> Optional[bytes]:
        try:
            page = self._get_page()
            if path:
                asyncio.run(page.screenshot(path=path, full_page=full_page))
                return path.encode()
            else:
                return asyncio.run(page.screenshot(full_page=full_page))
        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            return None

    def get_page_content(self, content_type: str = 'html') -> str:
        try:
            page = self._get_page()
            if content_type == 'html':
                return asyncio.run(page.content())
            else:
                return asyncio.run(page.inner_text('body'))
        except Exception as e:
            return ""

    def click(self, selector: str, timeout: Optional[int] = None, **kwargs) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.click(selector, timeout=timeout or self.timeout))
            return True
        except Exception as e:
            return False

    def type(self, selector: str, text: str, delay: int = 0, timeout: Optional[int] = None, **kwargs) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.fill(selector, ''))
            asyncio.run(page.type(selector, text, delay=delay))
            return True
        except Exception as e:
            return False

    def hover(self, selector: str, timeout: Optional[int] = None, **kwargs) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.hover(selector, timeout=timeout or self.timeout))
            return True
        except Exception as e:
            return False

    def wait_for_selector(self, selector: str, timeout: Optional[int] = None, state: str = 'visible', **kwargs) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.wait_for_selector(selector, timeout=timeout or self.timeout, state=state))
            return True
        except Exception as e:
            return False

    def execute_script(self, script: str, *args) -> Any:
        try:
            page = self._get_page()
            return asyncio.run(page.evaluate(script, *args))
        except Exception as e:
            self.logger.error(f"Execute script error: {e}")
            return None

    def get_cookies(self) -> List[Dict[str, Any]]:
        try:
            page = self._get_page()
            return asyncio.run(page.context.cookies())
        except Exception as e:
            return []

    def set_cookie(self, cookie: Dict[str, Any]) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.context.add_cookies([cookie]))
            return True
        except Exception as e:
            return False

    def delete_cookie(self, name: str, **kwargs) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.context.clear_cookies())
            return True
        except Exception as e:
            return False

    def get_local_storage(self) -> Dict[str, str]:
        try:
            page = self._get_page()
            return asyncio.run(page.evaluate("""() => {
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            }"""))
        except Exception:
            return {}

    def set_local_storage(self, key: str, value: str) -> bool:
        try:
            page = self._get_page()
            asyncio.run(page.evaluate(f"""(k, v) => {{ localStorage.setItem(k, v); }}""", key, value))
            return True
        except Exception:
            return False

    def close(self) -> None:
        try:
            if self._page:
                asyncio.run(self._page.close())
            if self._context:
                asyncio.run(self._context.close())
            if self._browser:
                asyncio.run(self._browser.close())
            if self._playwright:
                asyncio.run(self._playwright.stop())
        except Exception as e:
            self.logger.error(f"Close error: {e}")
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

    def __enter__(self):
        self._ensure_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
