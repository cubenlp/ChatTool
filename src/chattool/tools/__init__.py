import importlib


_LAZY_ATTRS = {
    "InteractiveShell": ("chattool.tools.interact", "InteractiveShell"),
    "SimpleAsyncShell": ("chattool.tools.interact", "SimpleAsyncShell"),
    "SSLCertUpdater": ("chatdns", "SSLCertUpdater"),
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
    "InteractiveShell", "SimpleAsyncShell",
    "SSLCertUpdater",
    "TPLogin",
]
