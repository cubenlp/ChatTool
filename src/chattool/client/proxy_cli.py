import click
import uvicorn
import logging
from chattool.utils import setup_logger

@click.command()
@click.option('--host', default='127.0.0.1', help='Bind address')
@click.option('--port', default=8000, help='Bind port')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def main(host, port, reload):
    """Start the Azure OpenAI Proxy Server"""
    logger = setup_logger('proxy_server')
    logger.info(f"Starting proxy server at {host}:{port}")
    
    uvicorn.run(
        "chattool.core.server:app",
        host=host,
        port=port,
        reload=reload
    )
