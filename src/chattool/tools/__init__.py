import importlib


_LAZY_ATTRS = {
    "ZulipClient": ("chattool.tools.zulip", "ZulipClient"),
    "GitHubClient": ("chattool.tools.github", "GitHubClient"),
    "InteractiveShell": ("chattool.tools.interact", "InteractiveShell"),
    "SimpleAsyncShell": ("chattool.tools.interact", "SimpleAsyncShell"),
    "create_dns_client": ("chattool.tools.dns", "create_dns_client"),
    "AliyunDNSClient": ("chattool.tools.dns", "AliyunDNSClient"),
    "TencentDNSClient": ("chattool.tools.dns", "TencentDNSClient"),
    "DynamicIPUpdater": ("chattool.tools.dns", "DynamicIPUpdater"),
    "SSLCertUpdater": ("chattool.tools.cert", "SSLCertUpdater"),
    "LarkBot": ("chattool.tools.lark", "LarkBot"),
    "ChatSession": ("chattool.tools.lark", "ChatSession"),
    "MessageContext": ("chattool.tools.lark", "MessageContext"),
    "TPLogin": ("chattool.tools.tplogin", "TPLogin"),
}


def __getattr__(name: str):
    target = _LAZY_ATTRS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(importlib.import_module(module_name), attr_name)
    globals()[name] = value
    return value

__all__ = [
    "ZulipClient", 
    "GitHubClient",
    "InteractiveShell", "SimpleAsyncShell",
    "create_dns_client",
    "AliyunDNSClient",
    "TencentDNSClient",
    "DynamicIPUpdater",
    "SSLCertUpdater",
    "LarkBot",
    "ChatSession",
    "MessageContext",
    "TPLogin",
]
