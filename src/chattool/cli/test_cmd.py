import click
from chattool.core.chattype import Chat, AzureChat
from chattool.tools.dns.aliyun import AliyunDNSClient
from chattool.tools.dns.tencent import TencentDNSClient
from chattool.tools.zulip.client import ZulipClient

def test_openai():
    click.echo("Testing OpenAI...")
    try:
        # 使用 max_tokens=5 减少消耗，仅测试连通性
        chat = Chat(messages=[{"role": "user", "content": "hi"}])
        resp = chat.get_response(max_tokens=5)
        click.echo(f"✅ Success! Response: {resp.content}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)

def test_azure():
    click.echo("Testing Azure OpenAI...")
    try:
        chat = AzureChat(messages=[{"role": "user", "content": "hi"}])
        resp = chat.get_response(max_tokens=5)
        click.echo(f"✅ Success! Response: {resp.content}")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)

def test_alidns():
    click.echo("Testing Aliyun DNS...")
    try:
        client = AliyunDNSClient()
        # 尝试获取域名列表，只取1个来验证
        domains = client.describe_domains(page_size=1)
        click.echo(f"✅ Success! API call successful. Found {len(domains)} domains (in first page).")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)

def test_tencent_dns():
    click.echo("Testing Tencent DNS...")
    try:
        client = TencentDNSClient()
        domains = client.describe_domains(page_size=1)
        click.echo(f"✅ Success! API call successful. Found {len(domains)} domains (in first page).")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)

def test_zulip():
    click.echo("Testing Zulip...")
    try:
        client = ZulipClient()
        profile = client.get_profile()
        click.echo(f"✅ Success! Authenticated as: {profile.get('email')} ({profile.get('full_name')})")
    except Exception as e:
        click.echo(f"❌ Failed: {e}", err=True)

@click.command(name='test')
@click.option('--target', '-t', required=True, type=click.Choice(['oai', 'openai', 'azure', 'az', 'ali', 'aliyun', 'alidns', 'tencent', 'tx', 'tencent-dns', 'zulip']), help='Target service to test.')
def test_cmd(target):
    """Test the configuration for a specific service.
    
    Supported aliases:
    - OpenAI: oai, openai
    - Azure: azure, az
    - Aliyun: ali, aliyun, alidns
    - Tencent: tencent, tx, tencent-dns
    - Zulip: zulip
    """
    if target in ['oai', 'openai']:
        test_openai()
    elif target in ['azure', 'az']:
        test_azure()
    elif target in ['ali', 'aliyun', 'alidns']:
        test_alidns()
    elif target in ['tencent', 'tx', 'tencent-dns']:
        test_tencent_dns()
    elif target == 'zulip':
        test_zulip()
