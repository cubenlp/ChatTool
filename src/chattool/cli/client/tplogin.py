import click
import json
from rich.console import Console
from rich.table import Table
from chattool.tools.tplogin import TPLogin

console = Console()

@click.group()
def cli():
    """TP-Link Router Tool"""
    pass

@cli.command()
def info():
    """获取设备信息"""
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

@cli.group(name="ufw", invoke_without_command=True)
@click.pass_context
def ufw(ctx):
    """虚拟服务器规则（ufw 风格）"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(ufw_list)

@ufw.command(name="list")
def ufw_list():
    """列出虚拟服务器规则"""
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
@click.option("--from-port", "src_port_start", type=int, required=True, help="外部端口起始")
@click.option("--from-port-end", "src_port_end", type=int, default=None, help="外部端口结束")
@click.option("--to-ip", "dest_ip", required=True, help="内网IP")
@click.option("--to-port", "dest_port", type=int, required=True, help="内部端口")
@click.option("--proto", type=click.Choice(["all", "tcp", "udp"]), default="all", show_default=True, help="协议")
def ufw_add(src_port_start, src_port_end, dest_ip, dest_port, proto):
    """添加虚拟服务器规则"""
    try:
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
