import click
import uvicorn
import logging
import os
from chattool.utils import setup_logger
from chattool.utils.config import AzureConfig

@click.command()
@click.option('--host', default='127.0.0.1', help='Bind address')
@click.option('--port', default=8000, help='Bind port')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.option('--api-base', default=None, help='Azure OpenAI API Base URL')
@click.option('--api-version', default=None, help='Azure OpenAI API Version')
def main(host, port, reload, api_base, api_version):
    """Start the Azure OpenAI Proxy Server"""
    logger = setup_logger('proxy_server')
    logger.info(f"Starting proxy server at {host}:{port}")
    
    # Set environment variables for the server process if provided
    if api_base:
        # Use config system to set environment variable implicitly via os.environ update if needed,
        # but here we update os.environ directly as AzureChat reads from env/config.
        # However, updating the config class memory doesn't affect os.environ for child processes unless we explicitly set it.
        # Since uvicorn runs in the same process (unless workers>1), setting os.environ is fine.
        # But to be consistent with config mechanism:
        AzureConfig.set(AzureConfig.AZURE_OPENAI_ENDPOINT.env_key, api_base)
        os.environ[AzureConfig.AZURE_OPENAI_ENDPOINT.env_key] = api_base
        logger.info(f"Overriding {AzureConfig.AZURE_OPENAI_ENDPOINT.env_key} with: {api_base}")
    
    if api_version:
        AzureConfig.set(AzureConfig.AZURE_OPENAI_API_VERSION.env_key, api_version)
        os.environ[AzureConfig.AZURE_OPENAI_API_VERSION.env_key] = api_version
        logger.info(f"Overriding {AzureConfig.AZURE_OPENAI_API_VERSION.env_key} with: {api_version}")

    uvicorn.run(
        "chattool.core.server:app",
        host=host,
        port=port,
        reload=reload
    )
