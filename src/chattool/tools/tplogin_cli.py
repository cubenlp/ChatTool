import click
import json
from rich.console import Console
from rich.table import Table
from chattool.interaction import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    resolve_command_inputs,
)
from chattool.tools.tplogin import TPLogin

console = Console()


UFW_RULE_SPEC_SCHEMA = CommandSchema(
    name="tplogin-ufw-rule-spec",
    fields=(CommandField("rule_spec", prompt="rule spec", required=True),),
)


@click.group()
def cli():
    """TP-Link router helpers."""
    pass


@cli.command()
def info():
    """Show router device info."""
    try:
        client = TPLogin()
        info = client.get_device_info()
        if info:
            click.echo(json.dumps(info, indent=2, ensure_ascii=False))
        else:
            click.echo("获取设备信息失败", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


def _render_ufw_table(rules):
    table = Table(title="TP-Link UFW 规则")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("NAME", style="blue")
    table.add_column("PROTO", style="green")
    table.add_column("EXT_PORT", style="yellow")
    table.add_column("INT_PORT", style="yellow")
    table.add_column("IP", style="magenta")

    for idx, rule in enumerate(rules, start=1):
        start = rule.get("src_dport_start", "")
        end = rule.get("src_dport_end", "")
        ext_port = start if start == end or not end else f"{start}-{end}"
        table.add_row(
            str(idx),
            rule.get("name", ""),
            str(rule.get("proto", "")).upper(),
            ext_port,
            rule.get("dest_port", ""),
            rule.get("dest_ip", ""),
        )
    console.print(table)


def _parse_rule_spec(rule_spec):
    parts = rule_spec.split(":")
    if len(parts) != 3:
        raise ValueError("规则格式应为 OUT_PORT:local_ip:IN_PORT")
    out_port_text, dest_ip, in_port_text = parts
    if "-" in out_port_text:
        start_text, end_text = out_port_text.split("-", 1)
        src_port_start = int(start_text)
        src_port_end = int(end_text)
    else:
        src_port_start = int(out_port_text)
        src_port_end = None
    dest_port = int(in_port_text)
    return src_port_start, src_port_end, dest_ip, dest_port


def _to_rule_spec(rule):
    start = str(rule.get("src_dport_start", ""))
    end = str(rule.get("src_dport_end", ""))
    out_port = start if start == end or not end else f"{start}-{end}"
    return f"{out_port}:{rule.get('dest_ip', '')}:{rule.get('dest_port', '')}"


def _signature_by_fields(src_port_start, src_port_end, dest_ip, dest_port, proto):
    end = src_port_end if src_port_end is not None else src_port_start
    return (
        str(src_port_start),
        str(end),
        str(dest_ip),
        str(dest_port),
        str(proto).lower(),
    )


def _signature_from_rule(rule):
    return (
        str(rule.get("src_dport_start", "")),
        str(rule.get("src_dport_end", "")),
        str(rule.get("dest_ip", "")),
        str(rule.get("dest_port", "")),
        str(rule.get("proto", "all")).lower(),
    )


@cli.group(name="ufw", invoke_without_command=True)
@click.pass_context
def ufw(ctx):
    """Manage virtual server rules with a ufw-style interface."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(ufw_status)


@ufw.command(name="status")
def ufw_status():
    """Show current virtual server rules."""
    try:
        client = TPLogin()
        rules = client.list_virtual_servers()
        if rules:
            _render_ufw_table(rules)
        else:
            click.echo("没有找到虚拟服务器规则")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@ufw.command(name="add")
@click.argument("rule_spec", type=str, required=False)
@click.option(
    "--proto",
    type=click.Choice(["all", "tcp", "udp"]),
    default="all",
    show_default=True,
    help="协议",
)
@add_interactive_option
def ufw_add(rule_spec, proto, interactive):
    """Add a virtual server rule: OUT_PORT:local_ip:IN_PORT."""
    inputs = resolve_command_inputs(
        schema=UFW_RULE_SPEC_SCHEMA,
        provided={"rule_spec": rule_spec},
        interactive=interactive,
        usage="Usage: chattool tplogin ufw add [RULE_SPEC] [-i|-I]",
    )
    rule_spec = inputs["rule_spec"]

    try:
        src_port_start, src_port_end, dest_ip, dest_port = _parse_rule_spec(rule_spec)
        client = TPLogin()
        ok = client.add_virtual_server(
            src_port_start=src_port_start,
            src_port_end=src_port_end,
            dest_ip=dest_ip,
            dest_port=dest_port,
            proto=proto,
        )
        if not ok:
            click.echo("添加失败", err=True)
            return
        click.echo("添加成功")
        rules = client.list_virtual_servers()
        _render_ufw_table(rules)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@ufw.command(name="dump")
@click.argument("path", required=False, default="tplogin_ufw_rules.json")
def ufw_dump(path):
    """Export virtual server rules to a file."""
    try:
        client = TPLogin()
        rules = client.list_virtual_servers()
        payload = {
            "format": "chattool.tplogin.ufw.v1",
            "rules": [
                {
                    "spec": _to_rule_spec(rule),
                    "proto": str(rule.get("proto", "all")).lower(),
                }
                for rule in rules
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        click.echo(f"已导出 {len(payload['rules'])} 条规则到: {path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@ufw.command(name="load")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--merge",
    is_flag=True,
    default=True,
    help="合并模式（默认）：跳过已存在的规则，仅添加新规则",
)
@click.option(
    "--delete",
    is_flag=True,
    help="清理模式：删除路由器中存在但文件中没有的规则，添加新规则",
)
@click.option(
    "--replace", is_flag=True, help="覆盖模式：删除所有现有规则，重新添加文件中的规则"
)
def ufw_load(path, merge, delete, replace):
    """Load virtual server rules from a file."""
    # 互斥检查
    if replace and delete:
        click.echo("错误: --replace 和 --delete 不能同时使用", err=True)
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            entries = data.get("rules", [])
        elif isinstance(data, list):
            entries = data
        else:
            raise ValueError("文件格式错误")

        # 1. 解析文件中的规则
        file_rules_parsed = []
        for entry in entries:
            if isinstance(entry, str):
                rule_spec = entry
                proto = "all"
            else:
                rule_spec = entry.get("spec", "")
                proto = str(entry.get("proto", "all")).lower()

            if not rule_spec:
                continue

            try:
                src_port_start, src_port_end, dest_ip, dest_port = _parse_rule_spec(
                    rule_spec
                )
                signature = _signature_by_fields(
                    src_port_start, src_port_end, dest_ip, dest_port, proto
                )
                file_rules_parsed.append(
                    {
                        "signature": signature,
                        "params": {
                            "src_port_start": src_port_start,
                            "src_port_end": src_port_end,
                            "dest_ip": dest_ip,
                            "dest_port": dest_port,
                            "proto": proto,
                        },
                    }
                )
            except Exception:
                click.echo(f"警告: 忽略无效规则 {rule_spec}", err=True)
                continue

        client = TPLogin()

        # 2. 获取当前规则
        current_rules = client.list_virtual_servers()
        current_map = {}  # signature -> rule_name
        for rule in current_rules:
            sig = _signature_from_rule(rule)
            current_map[sig] = rule.get("name")

        added = 0
        skipped = 0
        deleted = 0
        failed = 0

        # 3. 执行策略
        if replace:
            # 策略：删除所有现有规则，添加所有文件规则
            click.echo("模式: Replace (删除所有现有规则，重新添加)")
            with console.status("[bold red]正在清空现有规则..."):
                for name in current_map.values():
                    if client.delete_virtual_server(name):
                        deleted += 1
                    else:
                        click.echo(f"删除失败: {name}", err=True)

            # 重新获取当前规则（应为空）
            current_map = {}

        elif delete:
            # 策略：删除不在文件中的规则
            click.echo("模式: Delete (清理多余规则)")
            file_signatures = {r["signature"] for r in file_rules_parsed}
            to_delete = []
            for sig, name in current_map.items():
                if sig not in file_signatures:
                    to_delete.append(name)

            if to_delete:
                with console.status(
                    f"[bold red]正在清理 {len(to_delete)} 条多余规则..."
                ):
                    for name in to_delete:
                        if client.delete_virtual_server(name):
                            deleted += 1
                            # 从 current_map 中移除，避免影响后续判断（虽然其实不用）
                        else:
                            click.echo(f"删除失败: {name}", err=True)
            else:
                click.echo("没有需要清理的规则")
        else:
            # 默认 Merge 模式
            click.echo("模式: Merge (仅添加新规则，跳过已存在)")

        # 4. 添加规则
        with console.status("[bold green]正在应用规则..."):
            for item in file_rules_parsed:
                sig = item["signature"]
                params = item["params"]

                if sig in current_map:
                    # 已存在，跳过
                    skipped += 1
                    continue

                # 不存在，添加
                ok = client.add_virtual_server(**params)
                if ok:
                    added += 1
                    # 更新 current_map 以防文件中有重复规则
                    # 但我们不知道新规则的 name，所以只能假设它存在了
                    # 更好的做法是重新 fetch，但效率低。
                    # 这里主要防止文件自身重复导致重复添加
                    current_map[sig] = "newly_added"
                else:
                    failed += 1
                    click.echo(f"添加失败: {params}", err=True)

        click.echo(
            f"操作完成: added={added}, deleted={deleted}, skipped={skipped}, failed={failed}"
        )

        # 5. 显示最终结果
        final_rules = client.list_virtual_servers()
        if final_rules:
            _render_ufw_table(final_rules)
        else:
            click.echo("当前没有虚拟服务器规则")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@ufw.command(name="list", hidden=True)
def ufw_list():
    ufw_status()


@ufw.command(name="delete")
@click.option("--name", type=str, default=None, help="规则名，如 redirect_3")
@click.option("--id", "rule_id", type=int, default=None, help="表格中的 ID")
def ufw_delete(name, rule_id):
    """删除虚拟服务器规则"""
    try:
        client = TPLogin()
        rules = client.list_virtual_servers()
        target_name = name
        if target_name is None and rule_id is not None:
            if rule_id < 1 or rule_id > len(rules):
                click.echo("ID 超出范围", err=True)
                return
            target_name = rules[rule_id - 1].get("name")
        if not target_name:
            click.echo("请提供 --name 或 --id", err=True)
            return
        ok = client.delete_virtual_server(target_name)
        if not ok:
            click.echo("删除失败", err=True)
            return
        click.echo(f"删除成功: {target_name}")
        rules = client.list_virtual_servers()
        if rules:
            _render_ufw_table(rules)
        else:
            click.echo("当前没有虚拟服务器规则")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
