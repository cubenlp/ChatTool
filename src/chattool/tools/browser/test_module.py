#!/usr/bin/env python3
"""
Browser 客户端测试脚本
用于验证 Browser 工具模块的正确性。

这是手工 smoke script，不应阻塞自动化 pytest。
"""
from pathlib import Path
import sys
import types

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
BROWSER_DIR = REPO_ROOT / "src" / "chattool" / "tools" / "browser"
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

def setup_modules():
    """设置模块加载环境"""
    browser_pkg = types.ModuleType('chattool.tools.browser')
    browser_pkg.__path__ = [str(BROWSER_DIR)]
    
    sys.modules['chattool'] = types.ModuleType('chattool')
    sys.modules['chattool.tools'] = types.ModuleType('chattool.tools')
    sys.modules['chattool.tools.browser'] = browser_pkg
    
    import importlib.util
    
    # 加载 base
    spec = importlib.util.spec_from_file_location(
        'chattool.tools.browser.base', 
        BROWSER_DIR / 'base.py'
    )
    base = importlib.util.module_from_spec(spec)
    sys.modules['chattool.tools.browser.base'] = base
    browser_pkg.base = base
    spec.loader.exec_module(base)
    
    # 加载 playwright_impl
    spec = importlib.util.spec_from_file_location(
        'chattool.tools.browser.playwright_impl', 
        BROWSER_DIR / 'playwright_impl.py'
    )
    pw = importlib.util.module_from_spec(spec)
    sys.modules['chattool.tools.browser.playwright_impl'] = pw
    browser_pkg.pw = pw
    spec.loader.exec_module(pw)
    
    # 加载 selenium
    spec = importlib.util.spec_from_file_location(
        'chattool.tools.browser.selenium', 
        BROWSER_DIR / 'selenium.py'
    )
    sel = importlib.util.module_from_spec(spec)
    sys.modules['chattool.tools.browser.selenium'] = sel
    browser_pkg.sel = sel
    spec.loader.exec_module(sel)
    
    # 加载 __init__
    spec = importlib.util.spec_from_file_location(
        'chattool.tools.browser', 
        BROWSER_DIR / '__init__.py'
    )
    init = importlib.util.module_from_spec(spec)
    sys.modules['chattool.tools.browser'] = init
    spec.loader.exec_module(init)
    
    return init


def test_module_structure(module):
    """测试模块结构"""
    print("=" * 50)
    print("Testing Module Structure")
    print("=" * 50)
    
    # 检查导出的类
    assert hasattr(module, 'BrowserClient'), "BrowserClient not found"
    assert hasattr(module, 'PlaywrightBrowserClient'), "PlaywrightBrowserClient not found"
    assert hasattr(module, 'SeleniumBrowserClient'), "SeleniumBrowserClient not found"
    assert hasattr(module, 'AsyncPlaywrightBrowserClient'), "AsyncPlaywrightBrowserClient not found"
    assert hasattr(module, 'BrowserType'), "BrowserType not found"
    assert hasattr(module, 'create_browser_client'), "create_browser_client not found"
    
    print("✓ All required classes and functions found")
    
    # 检查 BrowserType 枚举
    assert len(module.BrowserType) == 3, f"Expected 3 browser types, got {len(module.BrowserType)}"
    print("✓ BrowserType enum correct")
    
    # 检查 BrowserClient 是抽象类
    import inspect
    assert inspect.isabstract(module.BrowserClient), "BrowserClient should be abstract"
    print("✓ BrowserClient is abstract")
    
    return True


def test_base_class_methods(module):
    """测试基类方法"""
    print("\n" + "=" * 50)
    print("Testing Base Class Methods")
    print("=" * 50)
    
    # 检查必须实现的抽象方法
    required_methods = [
        'goto', 'back', 'forward', 'refresh',
        'screenshot', 'get_page_content',
        'click', 'type', 'hover',
        'wait_for_selector', 'execute_script',
        'close', '__enter__', '__exit__'
    ]
    
    for method in required_methods:
        assert hasattr(module.BrowserClient, method), f"Method {method} not found"
    
    print(f"✓ All {len(required_methods)} required methods found")
    
    # 检查高级方法（应该有默认实现）
    advanced_methods = [
        'get_cookies', 'set_cookie', 'delete_cookie',
        'get_local_storage', 'set_local_storage',
        'fill_form', 'is_element_visible', 'check_links',
        'press_key', 'scroll_to', 'get_title', 'get_url'
    ]
    
    for method in advanced_methods:
        assert hasattr(module.BrowserClient, method), f"Method {method} not found"
    
    print(f"✓ All {len(advanced_methods)} advanced methods found")
    
    return True


def test_factory_function(module):
    """测试工厂函数"""
    print("\n" + "=" * 50)
    print("Testing Factory Function")
    print("=" * 50)
    
    # 测试创建 playwright 客户端
    client = module.create_browser_client(
        browser_type='playwright',
        headless=True,
        timeout=30000
    )
    assert isinstance(client, module.PlaywrightBrowserClient), "Wrong client type"
    print("✓ Playwright client created")
    
    # 测试创建异步客户端
    client = module.create_browser_client(
        browser_type='playwright_async',
        headless=True
    )
    assert isinstance(client, module.AsyncPlaywrightBrowserClient), "Wrong client type"
    print("✓ Async Playwright client created")
    
    # 测试创建 selenium 客户端
    client = module.create_browser_client(
        browser_type='selenium',
        headless=True
    )
    assert isinstance(client, module.SeleniumBrowserClient), "Wrong client type"
    print("✓ Selenium client created")
    
    # 测试便捷函数
    client = module.create_remote_browser_client(
        cdp_url='http://localhost:9222'
    )
    assert isinstance(client, module.PlaywrightBrowserClient), "Wrong client type"
    print("✓ Remote browser client created")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Browser Tool Module Test")
    print("=" * 60 + "\n")
    
    try:
        # 加载模块
        module = setup_modules()
        print("✓ Module loaded successfully\n")
        
        # 运行测试
        test_module_structure(module)
        test_base_class_methods(module)
        test_factory_function(module)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
        # 打印使用示例
        print("\nUsage Examples:")
        print("-" * 40)
        print("""
# 使用 Playwright 连接远程 CDP
client = create_browser_client(
    browser_type='playwright',
    cdp_url='http://rexpc.oray.wzhecnu.cn:9222'
)

# 使用 Playwright 本地浏览器
client = create_browser_client(
    browser_type='playwright',
    headless=False
)

# 使用 Selenium
client = create_browser_client(
    browser_type='selenium',
    browser='chrome'
)

# 使用示例
with client:
    client.goto('https://example.com')
    client.screenshot('page.png')
    content = client.get_page_content()
""")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
