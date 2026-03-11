"""
Selenium 浏览器客户端实现
支持本地和远程 WebDriver 连接
"""
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

from .base import BrowserClient


class SeleniumBrowserClient(BrowserClient):
    """Selenium 浏览器客户端"""
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        headless: bool = True,
        timeout: int = 30000,
        # Selenium 特定参数
        browser: str = 'chrome',  # chrome, firefox, edge
        driver_path: Optional[str] = None,  # WebDriver 路径
        remote_url: Optional[str] = None,   # 远程 WebDriver 地址
        options: Optional[Any] = None,       # 浏览器选项
        **kwargs
    ):
        """
        初始化 Selenium 浏览器客户端
        
        Args:
            logger: 日志记录器
            headless: 是否使用无头模式
            timeout: 默认超时时间
            browser: 浏览器类型
            driver_path: WebDriver 路径
            remote_url: 远程 WebDriver 地址 (如 'http://rexpc.oray.wzhecnu.cn:9222/wd/hub')
            options: 浏览器选项
        """
        super().__init__(logger=logger, headless=headless, timeout=timeout, **kwargs)
        
        self.browser = browser
        self.driver_path = driver_path
        self.remote_url = remote_url
        self._options = options
        self._driver = None
    
    def _ensure_driver(self) -> None:
        """确保 WebDriver 已启动"""
        if self._driver is None:
            self._init_driver()
    
    def _get_browser_options(self):
        """获取浏览器选项"""
        if self.browser.lower() == 'chrome':
            from selenium.webdriver.chrome.options import Options
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1280,720')
            return options
        elif self.browser.lower() == 'firefox':
            from selenium.webdriver.firefox.options import Options
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            return options
        elif self.browser.lower() == 'edge':
            from selenium.webdriver.edge.options import Options
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            return options
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")
    
    def _init_driver(self) -> None:
        """初始化 WebDriver"""
        browser_lower = self.browser.lower()
        
        # 如果提供了远程 URL，连接远程
        if self.remote_url:
            self.logger.info(f"Connecting to remote WebDriver: {self.remote_url}")
            
            from selenium import webdriver
            options = self._options or self._get_browser_options()
            if browser_lower not in {"chrome", "firefox", "edge"}:
                raise ValueError(f"Unsupported browser for remote: {self.browser}")
            self._driver = webdriver.Remote(
                command_executor=self.remote_url,
                options=options,
            )
        else:
            # 本地 WebDriver
            if browser_lower == 'chrome':
                from selenium import webdriver
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.chrome.options import Options
                
                options = self._options or self._get_browser_options()
                service = Service(executable_path=self.driver_path) if self.driver_path else None
                self._driver = webdriver.Chrome(service=service, options=options)
                
            elif browser_lower == 'firefox':
                from selenium import webdriver
                from selenium.webdriver.firefox.service import Service
                from selenium.webdriver.firefox.options import Options
                
                options = self._options or self._get_browser_options()
                service = Service(executable_path=self.driver_path) if self.driver_path else None
                self._driver = webdriver.Firefox(service=service, options=options)
                
            elif browser_lower == 'edge':
                from selenium import webdriver
                from selenium.webdriver.edge.service import Service
                from selenium.webdriver.edge.options import Options
                
                options = self._options or self._get_browser_options()
                service = Service(executable_path=self.driver_path) if self.driver_path else None
                self._driver = webdriver.Edge(service=service, options=options)
            else:
                raise ValueError(f"Unsupported browser: {self.browser}")
        
        # 设置隐式等待
        self._driver.implicitly_wait(self.timeout / 1000)
        # 设置页面加载超时
        self._driver.set_page_load_timeout(self.timeout / 1000)
        
        self.logger.info(f"Selenium {self.browser} driver initialized")
    
    def _get_driver(self):
        """获取当前 driver"""
        self._ensure_driver()
        return self._driver
    
    def _find_element(self, selector: str, timeout: Optional[int] = None):
        """查找元素"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        driver = self._get_driver()
        timeout_sec = (timeout or self.timeout) / 1000
        
        # 解析选择器
        by, value = self._parse_selector(selector)
        
        wait = WebDriverWait(driver, timeout_sec)
        return wait.until(EC.presence_of_element_located((by, value)))
    
    def _find_elements(self, selector: str):
        """查找多个元素"""
        from selenium.webdriver.common.by import By
        
        driver = self._get_driver()
        by, value = self._parse_selector(selector)
        return driver.find_elements(by, value)
    
    def _parse_selector(self, selector: str):
        """解析选择器为 Selenium By 类型"""
        from selenium.webdriver.common.by import By
        
        # 简单的选择器解析
        if selector.startswith('//'):
            return By.XPATH, selector
        elif selector.startswith('#'):
            return By.ID, selector[1:]
        elif selector.startswith('.'):
            return By.CLASS_NAME, selector[1:]
        elif '[' in selector and '=' in selector:
            # 属性选择器 [name=value]
            attr = selector[1:].split('=')[0]
            value = selector[selector.find('=') + 1:].strip('"\'')
            if attr == 'name':
                return By.NAME, value
            return By.CSS_SELECTOR, selector
        else:
            return By.CSS_SELECTOR, selector

    # ==================== 基础接口实现 ====================
    
    def goto(self, url: str, timeout: Optional[int] = None, **kwargs) -> bool:
        """导航到指定 URL"""
        try:
            driver = self._get_driver()
            self.logger.info(f"Navigating to: {url}")
            driver.get(url)
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate: {e}")
            return False

    def back(self) -> bool:
        """后退"""
        try:
            driver = self._get_driver()
            driver.back()
            return True
        except Exception as e:
            self.logger.error(f"Go back error: {e}")
            return False

    def forward(self) -> bool:
        """前进"""
        try:
            driver = self._get_driver()
            driver.forward()
            return True
        except Exception as e:
            self.logger.error(f"Go forward error: {e}")
            return False

    def refresh(self) -> bool:
        """刷新"""
        try:
            driver = self._get_driver()
            driver.refresh()
            return True
        except Exception as e:
            self.logger.error(f"Refresh error: {e}")
            return False

    def screenshot(self, path: Optional[str] = None, full_page: bool = False, **kwargs) -> Optional[bytes]:
        """截图"""
        try:
            driver = self._get_driver()
            
            if path:
                driver.save_screenshot(path)
                self.logger.info(f"Screenshot saved to: {path}")
                return path.encode()
            else:
                # 获取屏幕截图作为字节
                import base64
                screenshot_b64 = driver.get_screenshot_as_base64()
                return base64.b64decode(screenshot_b64)
        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            return None

    def get_page_content(self, content_type: str = 'html') -> str:
        """获取页面内容"""
        try:
            driver = self._get_driver()
            
            if content_type == 'html':
                return driver.page_source
            elif content_type == 'text':
                return driver.find_element('tag name', 'body').text
            else:
                return ""
        except Exception as e:
            self.logger.error(f"Get page content error: {e}")
            return ""

    def get_title(self) -> str:
        """获取页面标题"""
        try:
            driver = self._get_driver()
            return driver.title or ""
        except Exception:
            return ""

    def get_url(self) -> str:
        """获取当前 URL"""
        try:
            driver = self._get_driver()
            return driver.current_url or ""
        except Exception:
            return ""

    def click(self, selector: str, timeout: Optional[int] = None, **kwargs) -> bool:
        """点击元素"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            driver = self._get_driver()
            timeout_sec = (timeout or self.timeout) / 1000
            by, value = self._parse_selector(selector)
            
            wait = WebDriverWait(driver, timeout_sec)
            element = wait.until(EC.element_to_be_clickable((by, value)))
            element.click()
            self.logger.debug(f"Clicked: {selector}")
            return True
        except Exception as e:
            self.logger.error(f"Click error ({selector}): {e}")
            return False

    def type(self, selector: str, text: str, delay: int = 0, timeout: Optional[int] = None, **kwargs) -> bool:
        """输入文本"""
        try:
            import time
            element = self._find_element(selector, timeout)
            
            # 清空输入框
            element.clear()
            
            # 逐字符输入（如果指定了延迟）
            if delay > 0:
                for char in text:
                    element.send_keys(char)
                    time.sleep(delay / 1000)
            else:
                element.send_keys(text)
            
            self.logger.debug(f"Typed to: {selector}")
            return True
        except Exception as e:
            self.logger.error(f"Type error ({selector}): {e}")
            return False

    def hover(self, selector: str, timeout: Optional[int] = None, **kwargs) -> bool:
        """悬停"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            element = self._find_element(selector, timeout)
            driver = self._get_driver()
            
            ActionChains(driver).move_to_element(element).perform()
            self.logger.debug(f"Hovered: {selector}")
            return True
        except Exception as e:
            self.logger.error(f"Hover error ({selector}): {e}")
            return False

    def wait_for_selector(self, selector: str, timeout: Optional[int] = None, state: str = 'visible', **kwargs) -> bool:
        """等待元素"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            driver = self._get_driver()
            timeout_sec = (timeout or self.timeout) / 1000
            by, value = self._parse_selector(selector)
            quiet = kwargs.pop("quiet", False)
            
            wait = WebDriverWait(driver, timeout_sec)
            
            if state == 'visible':
                wait.until(EC.visibility_of_element_located((by, value)))
            elif state == 'hidden':
                wait.until(EC.invisibility_of_element_located((by, value)))
            elif state == 'attached':
                wait.until(EC.presence_of_element_located((by, value)))
                
            self.logger.debug(f"Element found: {selector}")
            return True
        except Exception as e:
            if not quiet:
                self.logger.error(f"Wait for selector error ({selector}): {e}")
            return False

    def execute_script(self, script: str, *args) -> Any:
        """执行 JavaScript"""
        try:
            driver = self._get_driver()
            return driver.execute_script(script, *args)
        except Exception as e:
            self.logger.error(f"Execute script error: {e}")
            return None

    # ==================== 高级接口实现 ====================
    
    def get_cookies(self) -> List[Dict[str, Any]]:
        """获取 cookies"""
        try:
            driver = self._get_driver()
            return [cookie for cookie in driver.get_cookies()]
        except Exception as e:
            self.logger.error(f"Get cookies error: {e}")
            return []

    def set_cookie(self, cookie: Dict[str, Any]) -> bool:
        """设置 cookie"""
        try:
            driver = self._get_driver()
            driver.add_cookie(cookie)
            self.logger.debug(f"Cookie set: {cookie.get('name')}")
            return True
        except Exception as e:
            self.logger.error(f"Set cookie error: {e}")
            return False

    def delete_cookie(self, name: str, **kwargs) -> bool:
        """删除 cookie"""
        try:
            driver = self._get_driver()
            driver.delete_cookie(name)
            self.logger.debug(f"Cookie deleted: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Delete cookie error: {e}")
            return False

    def get_local_storage(self) -> Dict[str, str]:
        """获取 localStorage"""
        try:
            driver = self._get_driver()
            script = """
                var items = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            """
            return driver.execute_script(script) or {}
        except Exception as e:
            self.logger.error(f"Get localStorage error: {e}")
            return {}

    def set_local_storage(self, key: str, value: str) -> bool:
        """设置 localStorage"""
        try:
            driver = self._get_driver()
            driver.execute_script(f"localStorage.setItem('{key}', '{value}')")
            self.logger.debug(f"localStorage set: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Set localStorage error: {e}")
            return False

    def press_key(self, key: str, **kwargs) -> bool:
        """模拟按键"""
        try:
            from selenium.webdriver.common.keys import Keys
            
            driver = self._get_driver()
            
            # 处理特殊键
            key_mapping = {
                'Enter': Keys.RETURN,
                'Escape': Keys.ESCAPE,
                'Tab': Keys.TAB,
                'Backspace': Keys.BACKSPACE,
                'Delete': Keys.DELETE,
                'Ctrl+C': Keys.CONTROL + 'c',
                'Ctrl+V': Keys.CONTROL + 'v',
            }
            
            key_obj = key_mapping.get(key, key)
            driver.switch_to.active_element.send_keys(key_obj)
            self.logger.debug(f"Key pressed: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Press key error: {e}")
            return False

    # ==================== 生命周期管理 ====================
    
    def close(self) -> None:
        """关闭浏览器"""
        try:
            if self._driver:
                self._driver.quit()
                self._driver = None
                self.logger.info("Browser closed")
        except Exception as e:
            self.logger.error(f"Close browser error: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        self._ensure_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False
