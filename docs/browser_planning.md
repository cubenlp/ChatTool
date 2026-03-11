# Browser Tool 规划

## 目标

在 ChatTool 中提供 Browser 自动化工具能力，基于 Chrome DevTools Protocol (CDP) 实现无头浏览器操作。

## 功能范围

### 1. 基础能力
- **页面导航**: goto, back, forward, refresh
- **元素操作**: click, type, hover, drag
- **截图**: 整页截图、区域截图
- **获取页面内容**: HTML, text, 元素信息

### 2. 高级能力
- **等待策略**: 等待元素出现/消失、等待网络空闲
- **表单处理**: 自动填写表单、提交
- **Cookie/Storage**: 读取、设置、删除
- **JavaScript 执行**: 注入并执行自定义 JS

### 3. 调试/测试能力
- **有效性测试**: 检测页面元素是否存在
- **链接有效性**: 检查页面链接是否可访问
- **性能指标**: 加载时间等基础指标

## 技术选型

- **Playwright**: 推荐首选，CDP 封装完善，支持 Python
- **Selenium**: 备选方案
- **直接 CDP**: 底层协议，可用于特殊场景

## 目录结构

```
src/chattool/tools/browser/
├── __init__.py          # 导出入口
├── base.py              # 抽象基类
├── playwright_.py       # Playwright 实现
├── config.py            # 配置管理
└── debug.py             # 调试工具
```

## 实现步骤

1. **Phase 1 - 基础框架**
   - 创建目录结构
   - 实现 base.py 抽象类
   - 实现配置管理

2. **Phase 2 - 核心功能**
   - 实现 Playwright 包装器
   - 基础页面操作 (导航、截图)
   - 元素定位与操作

3. **Phase 3 - 高级功能**
   - 等待策略
   - 表单处理
   - Cookie/Storage 操作

4. **Phase 4 - 调试能力**
   - 有效性测试接口
   - 链接检查
   - 日志与调试工具

## 待确认

- [ ] 使用哪个 CDP 客户端库？ (Playwright / Selenium / 其他)
- [ ] 调试地址: `rexpc.oray.wzhecnu.cn:9222` (由用户提供)
- [ ] 是否需要支持多浏览器实例池？
- [ ] 是否需要集成到现有 tool 注册机制？

---

**请审阅上述规划，确认后给我调试链接进行测试。**
