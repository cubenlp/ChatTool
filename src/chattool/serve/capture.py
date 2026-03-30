from __future__ import annotations

import click
from fastapi import FastAPI, Request
from datetime import datetime

from chattool.utils import generate_curl_command, FastAPIManager

app = FastAPI(
    title="请求监控 API",
    description="捕获并展示所有 HTTP 请求的详细信息",
    version="1.0.0"
)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def capture_all_requests(request: Request, path: str = ""):
    """
    捕获所有进入的 HTTP 请求并返回详细信息
    
    - path: 请求路径（支持任意深度的路径）
    - request: 请求对象，包含所有请求相关信息
    """
    # 获取请求时间
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 获取请求体（如果有）
    body = await request.body()
    body_str = body.decode('utf-8') if body else ""
    
    # 构建请求信息
    request_info = {
        "timestamp": timestamp,
        "method": request.method,
        "url": str(request.url),
        "path": path,
        "client": {
            "host": request.client.host,
            "port": request.client.port
        },
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "body": body_str
    }
    
    # 生成 curl 命令
    curl_command = generate_curl_command(request_info)
    
    # 打印请求信息到控制台
    print("\n" + "="*50)
    print(f"📝 新请求 | {timestamp}")
    print(f"📌 方法: {request.method}")
    print(f"🔗 URL: {request.url}")
    print(f"👤 客户端: {request.client.host}:{request.client.port}")
    print(f"🔍 查询参数: {dict(request.query_params)}")
    if body_str:
        print(f"📦 请求体: {body_str}")
    print(f"📋 请求头:")
    for key, value in request.headers.items():
        print(f"   {key}: {value}")
    
    # 打印 curl 命令
    print(f"\n🔧 等效 curl 命令:")
    print(curl_command)
    print("="*50)
    
    return {
        "status": "success",
        "message": "请求已收到",
        "request_info": request_info,
        "curl_command": curl_command
    }

@click.command()
@click.option('--host', default='0.0.0.0', help='服务器监听地址')
@click.option('--port', default=8000, help='服务器监听端口')
@click.option('--daemon', '-d', is_flag=True, help='后台运行模式（使用线程）')
@click.option('--reload', is_flag=True, help='启用自动重载')
def main(host, port, daemon, reload):
    """
    启动请求捕获服务器
    
    支持两种运行模式：
    1. 直接运行模式（默认）：阻塞主线程，适合开发调试
    2. 后台运行模式（--daemon）：使用线程后台运行，适合集成到其他应用
    """
    import signal
    import sys
    import time
    
    click.echo("🚀 启动请求捕获服务器...")
    click.echo("📡 服务器将监听所有进入的 HTTP 请求")
    click.echo(f"🔗 访问 http://{host}:{port}/docs 查看 API 文档")
    click.echo("⏹️  按 Ctrl+C 停止服务器")
    
    if daemon:
        # 后台运行模式 - 使用 FastAPIManager
        click.echo("🔧 使用后台线程模式启动...")
        
        manager = FastAPIManager(app, host=host, port=port, reload=reload)
        
        def signal_handler(sig, frame):
            click.echo("\n🛑 正在停止服务器...")
            manager.stop()
            sys.exit(0)
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 启动服务器
        manager.start()
        
        try:
            # 保持主线程运行
            while manager.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\n🛑 正在停止服务器...")
            manager.stop()
    else:
        # 直接运行模式 - 使用 uvicorn.run
        click.echo("🔧 使用直接运行模式启动...")
        
        import uvicorn
        
        try:
            uvicorn.run(
                app,
                host=host,
                port=port,
                reload=reload,
                log_level="info"
            )
        except KeyboardInterrupt:
            click.echo("\n🛑 服务器已停止")
    

if __name__ == "__main__":
    main()
