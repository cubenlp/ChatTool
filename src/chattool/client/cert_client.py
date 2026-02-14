import click
import requests
import os
from rich.console import Console
from rich.table import Table
from typing import Optional

console = Console()

@click.group(name="cert")
@click.option('--server', default='http://127.0.0.1:8000', help='SSL 证书服务地址')
@click.option('-t', '--token', help='鉴权 Token (也可通过 CHATTOOL_CERT_TOKEN 环境变量设置)')
@click.pass_context
def cert_client(ctx, server, token):
    """SSL 证书客户端工具 (连接到 chattool serve cert)"""
    ctx.ensure_object(dict)
    ctx.obj['SERVER'] = server
    # 优先使用命令行参数，其次环境变量
    ctx.obj['TOKEN'] = token or os.environ.get('CHATTOOL_CERT_TOKEN')
    
    if not ctx.obj['TOKEN']:
        console.print("[yellow]警告: 未提供 Token，某些操作可能会失败。请使用 --token 或设置 CHATTOOL_CERT_TOKEN[/yellow]")

@cert_client.command()
@click.option('-d', '--domain', 'domains', multiple=True, required=True, help='域名 (可多次使用，例如 -d example.com -d *.example.com)')
@click.option('-e', '--email', required=True, help='Let\'s Encrypt 邮箱')
@click.option('-p', '--provider', type=click.Choice(['aliyun', 'tencent']), help='DNS 提供商 (可选，覆盖服务端默认)')
@click.option('--secret-id', help='云厂商 Secret ID (可选)')
@click.option('--secret-key', help='云厂商 Secret Key (可选)')
@click.pass_context
def apply(ctx, domains, email, provider, secret_id, secret_key):
    """申请 SSL 证书"""
    server = ctx.obj['SERVER']
    token = ctx.obj['TOKEN']
    headers = {"X-ChatTool-Token": token} if token else {}
    
    payload = {
        "domains": list(domains),
        "email": email,
        "provider": provider,
        "secret_id": secret_id,
        "secret_key": secret_key
    }
    # 移除 None 值
    payload = {k: v for k, v in payload.items() if v is not None}
    
    try:
        with console.status(f"[bold green]正在提交申请: {', '.join(domains)}..."):
            resp = requests.post(f"{server}/cert/apply", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
        console.print(f"[bold green]✅ 申请已提交![/bold green]")
        console.print(f"状态: {data.get('status')}")
        console.print(f"消息: {data.get('message')}")
        console.print("\n请稍后使用 `chattool client cert list` 查看结果。")
        
    except requests.RequestException as e:
        console.print(f"[bold red]❌ 请求失败: {e}[/bold red]")
        if hasattr(e, 'response') and e.response:
             console.print(f"服务端响应: {e.response.text}")

@cert_client.command(name="list")
@click.pass_context
def list_certs(ctx):
    """列出已申请的证书"""
    server = ctx.obj['SERVER']
    token = ctx.obj['TOKEN']
    headers = {"X-ChatTool-Token": token} if token else {}
    
    try:
        with console.status("[bold green]正在获取证书列表..."):
            resp = requests.get(f"{server}/cert/list", headers=headers)
            resp.raise_for_status()
            certs = resp.json()
            
        if not certs:
            console.print("[yellow]没有找到任何证书记录。[/yellow]")
            return
            
        table = Table(title="SSL 证书列表")
        table.add_column("主域名", style="cyan")
        table.add_column("包含域名", style="blue")
        table.add_column("生成时间", style="green")
        table.add_column("过期时间", style="yellow")
        table.add_column("剩余天数", justify="right")
        
        for cert in certs:
            table.add_row(
                cert.get('domain'),
                ", ".join(cert.get('domains', [])),
                cert.get('created_at', 'N/A')[:19], # 截断微秒
                cert.get('expires_at', 'N/A')[:10], # 只显示日期
                str(cert.get('days_remaining', 'N/A'))
            )
            
        console.print(table)
        
    except requests.RequestException as e:
        console.print(f"[bold red]❌ 请求失败: {e}[/bold red]")

@cert_client.command()
@click.argument('domain')
@click.option('-o', '--output-dir', default='.', help='下载保存目录')
@click.pass_context
def download(ctx, domain, output_dir):
    """下载证书文件 (cert.pem, privkey.pem)"""
    server = ctx.obj['SERVER']
    token = ctx.obj['TOKEN']
    headers = {"X-ChatTool-Token": token} if token else {}
    
    target_dir = os.path.join(output_dir, domain)
    os.makedirs(target_dir, exist_ok=True)
    
    files = ["cert.pem", "privkey.pem", "fullchain.pem", "chain.pem"] # 尝试下载常见文件
    success_count = 0
    
    console.print(f"正在下载证书到: [bold]{target_dir}[/bold]")
    
    for filename in files:
        try:
            url = f"{server}/cert/download/{domain}/{filename}"
            # console.print(f"下载: {url}")
            resp = requests.get(url, headers=headers, stream=True)
            
            if resp.status_code == 200:
                file_path = os.path.join(target_dir, filename)
                with open(file_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                console.print(f"  ✅ {filename}")
                success_count += 1
            elif resp.status_code == 404:
                # 某些文件可能不存在，忽略
                pass
            else:
                console.print(f"  ❌ {filename} (HTTP {resp.status_code})")
                
        except requests.RequestException as e:
            console.print(f"  ❌ {filename}: {e}")
            
    if success_count > 0:
        console.print(f"\n[bold green]成功下载 {success_count} 个文件。[/bold green]")
    else:
        console.print(f"\n[bold red]下载失败，未找到任何文件。[/bold red]")

if __name__ == '__main__':
    cert_client()
