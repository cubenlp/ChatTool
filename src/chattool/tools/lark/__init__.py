import importlib


_LAZY_ATTRS = {
    "LarkBot": ("chattool.tools.lark.bot", "LarkBot"),
    "MessageContext": ("chattool.tools.lark.context", "MessageContext"),
    "DocxBlockType": ("chattool.tools.lark.docx_blocks", "DocxBlockType"),
    "parse_markdown_blocks": ("chattool.tools.lark.markdown_blocks", "parse_markdown_blocks"),
    "ChatSession": ("chattool.tools.lark.session", "ChatSession"),
}


def __getattr__(name: str):
    target = _LAZY_ATTRS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    value = getattr(importlib.import_module(module_name), attr_name)
    globals()[name] = value
    return value

__all__ = ["LarkBot", "MessageContext", "ChatSession", "DocxBlockType", "parse_markdown_blocks"]
