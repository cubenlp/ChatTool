import importlib


_LAZY_ATTRS = {
    "capture_app": ("chattool.serve.capture", "app"),
    "capture_main": ("chattool.serve.capture", "main"),
    "cert_app": ("chattool.serve.cert_server", "cert_app"),
    "serve_cli": ("chattool.serve.cli", "serve_cli"),
    "lark_serve_cli": ("chattool.serve.lark_serve", "cli"),
    "svg2gif_app": ("chattool.serve.svg2gif", "svg2gif_app"),
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
    "capture_app",
    "capture_main",
    "cert_app",
    "serve_cli",
    "lark_serve_cli",
    "svg2gif_app",
]
