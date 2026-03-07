from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class MCPToolSpec:
    name: str
    module: str
    tags: Sequence[str]
    summary: str


TOOL_SPECS: Sequence[MCPToolSpec] = (
    MCPToolSpec("dns_list_domains", "dns", ("dns", "read"), "列出 DNS 域名"),
    MCPToolSpec("dns_get_records", "dns", ("dns", "read"), "查询 DNS 记录"),
    MCPToolSpec("dns_add_record", "dns", ("dns", "write"), "添加 DNS 记录"),
    MCPToolSpec("dns_delete_record", "dns", ("dns", "write"), "删除 DNS 记录"),
    MCPToolSpec("dns_ddns_update", "dns", ("dns", "write"), "执行 DDNS 更新"),
    MCPToolSpec("dns_cert_update", "dns", ("cert", "write"), "申请或续期证书"),
    MCPToolSpec("zulip_list_streams", "zulip", ("zulip", "read"), "列出 Zulip 频道"),
    MCPToolSpec("zulip_get_messages", "zulip", ("zulip", "read"), "查询 Zulip 消息"),
    MCPToolSpec("zulip_send_message", "zulip", ("zulip", "write"), "发送 Zulip 消息"),
    MCPToolSpec("zulip_react", "zulip", ("zulip", "write"), "添加 Zulip 表情反应"),
    MCPToolSpec("zulip_upload_file", "zulip", ("zulip", "write"), "上传 Zulip 文件"),
    MCPToolSpec("network_ping_scan", "network", ("network", "read"), "扫描在线主机"),
    MCPToolSpec("network_port_scan", "network", ("network", "read"), "扫描端口开放主机"),
)


def get_tool_specs() -> List[MCPToolSpec]:
    return list(TOOL_SPECS)


def get_visible_tool_specs(
    enable_tags: Iterable[str] | None = None,
    disable_tags: Iterable[str] | None = None,
) -> List[MCPToolSpec]:
    enabled = {t.strip() for t in (enable_tags or []) if t and t.strip()}
    disabled = {t.strip() for t in (disable_tags or []) if t and t.strip()}
    result = []
    for spec in TOOL_SPECS:
        tag_set = set(spec.tags)
        if enabled and not (tag_set & enabled):
            continue
        if disabled and (tag_set & disabled):
            continue
        result.append(spec)
    return result
