import click
import uvicorn
import logging
import os
from chattool.utils import setup_logger
from chattool.utils.config import AzureConfig
from chattool.adapter import ADAPTERS

@click.group()
@click.option('--host', default='127.0.0.1', help='Bind address')
@click.option('--port', default=8000, help='Bind port')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.pass_context
def main(ctx, host, port, reload):
    """Start a Model Proxy Server"""
    ctx.ensure_object(dict)
    ctx.obj['host'] = host
    ctx.obj['port'] = port
    ctx.obj['reload'] = reload
    setup_logger('proxy_server')

def create_adapter_command(name):
    @click.command(name=name)
    @click.option('--api-base', default=None, help='Backend API Base URL')
    @click.option('--api-version', default=None, help='Backend API Version')
    @click.pass_context
    def cmd(ctx, api_base, api_version):
        """Start the {name} proxy server""".format(name=name)
        host = ctx.obj['host']
        port = ctx.obj['port']
        reload = ctx.obj['reload']
        
        logger = logging.getLogger('proxy_server')
        logger.info(f"Starting {name} proxy server at {host}:{port}")
        
        # Set environment variables if provided
        if api_base:
            # Note: This might need to be more specific based on the adapter
            # but for now we'll set the common ones
            os.environ['OPENAI_API_BASE'] = api_base
            os.environ['AZURE_OPENAI_ENDPOINT'] = api_base
        if api_version:
            os.environ['AZURE_OPENAI_API_VERSION'] = api_version

        uvicorn.run(
            f"chattool.adapter.{name}:app",
            host=host,
            port=port,
            reload=reload
        )
    return cmd

# Add subcommands for each adapter
for adapter_name in ADAPTERS.keys():
    main.add_command(create_adapter_command(adapter_name))

# For backward compatibility or default behavior, we could keep a default command
# but the user explicitly asked for the new style.
