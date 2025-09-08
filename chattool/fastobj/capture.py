from fastapi import FastAPI, Request
from datetime import datetime
from chattool.fastobj.basic import generate_curl_command
import uvicorn

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
