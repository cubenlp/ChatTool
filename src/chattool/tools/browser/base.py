"""
Browser 客户端抽象基类
定义统一的浏览器自动化接口
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Union
from pathlib import Path


class BrowserClient(ABC):
    """浏览器客户端抽象基类"""
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        headless: bool = True,
        timeout: int = 30000,
        **kwargs
    ):
        """
        初始化浏览器客户端
        
        Args:
            logger: 日志记录器
            headless: 是否使用无头模式
            timeout: 默认超时时间（毫秒）
        """
        self.logger = logger or logging.getLogger(__name__)
        self.headless = headless
        self.timeout = timeout
        self._page = None
        self._browser = None

    # ==================== 基础接口 (必须实现) ====================
    
    @abstractmethod
    def goto(self, url: str, timeout: Optional[int] = None, **kwargs) -> bool:
        """
        导航到指定 URL
        
        Args:
            url: 目标 URL
            timeout: 超时时间（毫秒）
            **kwargs: 其他参数
            
        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def back(self) -> bool:
        """后退到上一页"""
        pass

    @abstractmethod
    def forward(self) -> bool:
        """前进到下一页"""
        pass

    @abstractmethod
    def refresh(self) -> bool:
        """刷新当前页"""
        pass

    @abstractmethod
    def screenshot(self, path: Optional[str] = None, full_page: bool = False, **kwargs) -> Optional[bytes]:
        """
        截图
        
        Args:
            path: 保存路径（如果为 None，返回字节数据）
            full_page: 是否截取整个页面
            **kwargs: 其他参数
            
        Returns:
            字节数据或文件路径
        """
        pass

    @abstractmethod
    def get_page_content(self, content_type: str = 'html') -> str:
        """
        获取页面内容
        
        Args:
            content_type: 内容类型 ('html' 或 'text')
            
        Returns:
            页面 HTML 或文本
        """
        pass

    @abstractmethod
    def click(self, selector: str, timeout: Optional[int] = None, **kwargs) -> bool:
        """
        点击元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间
            **kwargs: 其他参数
            
        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def type(self, selector: str, text: str, delay: int = 0, timeout: Optional[int] = None, **kwargs) -> bool:
        """
        输入文本
        
        Args:
            selector: 元素选择器
            text: 输入的文本
            delay: 输入延迟（毫秒）
            timeout: 超时时间
            **kwargs: 其他参数
            
        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def hover(self, selector: str, timeout: Optional[int] = None, **kwargs) -> bool:
        """
        悬停在元素上
        
        Args:
            selector: 元素选择器
            timeout: 超时时间
            **kwargs: 其他参数
            
        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def wait_for_selector(self, selector: str, timeout: Optional[int] = None, state: str = 'visible', **kwargs) -> bool:
        """
        等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间
            state: 状态 ('visible', 'hidden', 'attached', 'detached')
            
        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def execute_script(self, script: str, *args) -> Any:
        """
        执行 JavaScript
        
        Args:
            script: JavaScript 代码
            *args: 传递给脚本的参数
            
        Returns:
            脚本执行结果
        """
        pass

    # ==================== 高级接口 (提供默认实现) ====================
    
    def get_cookies(self) -> List[Dict[str, Any]]:
        """
        获取当前页面 cookies
        
        Returns:
            Cookie 列表
        """
        self.logger.warning("get_cookies not implemented in this browser client")
        return []

    def set_cookie(self, cookie: Dict[str, Any]) -> bool:
        """
        设置 cookie
        
        Args:
            cookie: Cookie 字典
            
        Returns:
            是否成功
        """
        self.logger.warning("set_cookie not implemented in this browser client")
        return False

    def delete_cookie(self, name: str, **kwargs) -> bool:
        """
        删除 cookie
        
        Args:
            name: Cookie 名称
            **kwargs: 其他参数
            
        Returns:
            是否成功
        """
        self.logger.warning("delete_cookie not implemented in this browser client")
        return False

    def get_local_storage(self) -> Dict[str, str]:
        """
        获取 localStorage
        
        Returns:
            localStorage 内容
        """
        self.logger.warning("get_local_storage not implemented in this browser client")
        return {}

    def set_local_storage(self, key: str, value: str) -> bool:
        """
        设置 localStorage
        
        Args:
            key: 键
            value: 值
            
        Returns:
            是否成功
        """
        self.logger.warning("set_local_storage not implemented in this browser client")
        return False

    def fill_form(self, selector: str, data: Dict[str, str], timeout: Optional[int] = None) -> bool:
        """
        填写表单
        
        Args:
            selector: 表单选择器
            data: 表单数据 {selector: value, ...}
            timeout: 超时时间
            
        Returns:
            是否成功
        """
        try:
            for field_selector, value in data.items():
                # 尝试不同的输入方式
                if not self.type(field_selector, value, timeout=timeout):
                    self.logger.warning(f"Failed to fill field: {field_selector}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Fill form error: {e}")
            return False

    def is_element_visible(self, selector: str) -> bool:
        """
        检查元素是否可见
        
        Args:
            selector: 元素选择器
            
        Returns:
            是否可见
        """
        try:
            script = """
                const el = document.querySelector(arguments[0]);
                if (!el) return false;
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       style.opacity !== '0' &&
                       el.offsetParent !== null;
            """
            result = self.execute_script(script, selector)
            return bool(result)
        except Exception as e:
            self.logger.error(f"Check element visibility error: {e}")
            return False

    def check_links(self, timeout: int = 5000) -> Dict[str, Any]:
        """
        检查页面链接有效性
        
        Args:
            timeout: 每个链接的超时时间
            
        Returns:
            {'valid': [...], 'invalid': [...], 'total': N}
        """
        try:
            # 获取所有链接
            script = """
                Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(href => href.startsWith('http'))
            """
            links = self.execute_script(script)
            if not links:
                return {'valid': [], 'invalid': [], 'total': 0}
            
            # 简单的 JavaScript 验证（检查响应状态）
            # 注意：这只是客户端检测，不一定准确
            valid = []
            invalid = []
            
            for link in links:
                # 由于跨域限制，这里只做基本检查
                # 实际验证需要服务端支持
                if link.startswith(('http://', 'https://')):
                    valid.append(link)
                else:
                    invalid.append(link)
            
            return {
                'valid': valid,
                'invalid': invalid,
                'total': len(links)
            }
        except Exception as e:
            self.logger.error(f"Check links error: {e}")
            return {'valid': [], 'invalid': [], 'total': 0}

    def press_key(self, key: str, **kwargs) -> bool:
        """
        模拟按键
        
        Args:
            key: 键名 (如 'Enter', 'Escape', 'Ctrl+C')
            **kwargs: 其他参数
            
        Returns:
            是否成功
        """
        self.logger.warning("press_key not implemented in this browser client")
        return False

    def scroll_to(self, x: int = 0, y: int = 0) -> bool:
        """
        滚动到指定位置
        
        Args:
            x: X 坐标
            y: Y 坐标
            
        Returns:
            是否成功
        """
        try:
            self.execute_script(f"window.scrollTo({x}, {y})")
            return True
        except Exception as e:
            self.logger.error(f"Scroll error: {e}")
            return False

    def get_title(self) -> str:
        """获取页面标题"""
        try:
            return self.execute_script("document.title") or ""
        except Exception:
            return ""

    def get_url(self) -> str:
        """获取当前 URL"""
        try:
            return self.execute_script("window.location.href") or ""
        except Exception:
            return ""

    # ==================== 生命周期管理 ====================
    
    @abstractmethod
    def close(self) -> None:
        """关闭浏览器"""
        pass

    @abstractmethod
    def __enter__(self):
        """上下文管理器入口"""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        pass

    # ==================== 工具方法 ====================
    
    def wait(self, milliseconds: int) -> None:
        """
        等待指定时间
        
        Args:
            milliseconds: 毫秒数
        """
        import time
        time.sleep(milliseconds / 1000)
