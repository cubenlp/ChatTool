import click
import uvicorn
from chattool.tools.cert.cert_server import app, config

@click.command(name="cert")
@click.option('--host', default='0.0.0.0', help='监听地址')
@click.option('--port', '-p', default=8000, help='监听端口')
@click.option('--output', '-o', default='certs', help='证书存储根目录')
@click.option('--provider', default='aliyun', type=click.Choice(['aliyun', 'tencent']), help='默认 DNS 提供商')
@click.option('--secret-id', help='默认云厂商 Secret ID')
@click.option('--secret-key', help='默认云厂商 Secret Key')
def cert_app(host, port, output, provider, secret_id, secret_key):
    """
    启动 SSL 证书服务 (API)
    
    提供证书的异步申请和安全下载功能。
    支持多租户隔离：不同 Token 的数据存储在不同目录下。
    """
    # 更新全局配置
    config["cert_dir"] = output
    config["provider"] = provider
    config["secret_id"] = secret_id
    config["secret_key"] = secret_key
    
    click.echo(f"🚀 启动 SSL 证书服务 (多租户模式)")
    click.echo(f"📡 监听: http://{host}:{port}")
    click.echo(f"📂 证书根目录: {output}")
    click.echo(f"🔒 安全机制: 基于 Token 哈希的目录隔离")
    
    uvicorn.run(app, host=host, port=port)
