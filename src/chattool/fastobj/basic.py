import json
import asyncio
import threading
import uvicorn
from typing import Optional, List

def generate_curl_command(request_info: dict) -> str:
    """
    根据请求信息生成对应的 curl 命令
    """
    method = request_info["method"]
    url = request_info["url"]
    headers = request_info["headers"]
    body = request_info["body"]
    
    # 构建基础 curl 命令
    curl_cmd = f"curl -X {method} '{url}' \\"
    
    # 添加请求头（排除一些自动生成的头）
    skip_headers = {
        'host', 'content-length', 'connection', 'accept-encoding',
        'user-agent'  # 可根据需要调整要跳过的头
    }
    
    for key, value in headers.items():
        if key.lower() not in skip_headers:
            curl_cmd += f"\n    -H '{key}: {value}' \\"
    
    # 如果有请求体，添加 Content-Type 和数据
    if body:
        # 如果没有显式的 Content-Type，尝试推断
        if 'content-type' not in [h.lower() for h in headers.keys()]:
            try:
                # 尝试解析为 JSON
                json.loads(body)
                curl_cmd += f"\n    -H 'Content-Type: application/json' \\"
            except json.JSONDecodeError:
                curl_cmd += f"\n    -H 'Content-Type: text/plain' \\"
        
        # 添加请求体数据
        if body.strip().startswith('{') and body.strip().endswith('}'):
            # 格式化 JSON 数据
            try:
                formatted_body = json.dumps(json.loads(body), ensure_ascii=False, separators=(',', ':'))
                curl_cmd += f"\n    -d '{formatted_body}' \\"
            except json.JSONDecodeError:
                curl_cmd += f"\n    -d '{body}' \\"
        else:
            curl_cmd += f"\n    -d '{body}' \\"
    
    return curl_cmd.rstrip(" \\")

class FastAPIManager:
    def __init__(self, app, host: str = ["0.0.0.0", "::"], port: int = 8000, **kwargs):
        self.app = app
        self.host = host
        self.port = port
        self.kwargs = kwargs
        self.server: Optional[uvicorn.Server] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
    
    def start(self):
        """启动服务（后台运行）"""
        if self.is_running:
            print("服务已在运行中")
            return
        
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            **self.kwargs
        )
        self.server = uvicorn.Server(config)
        
        def run_server():
            asyncio.run(self.server.serve())
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        self.is_running = True
        print(f"🚀 服务已启动: http://{self.host}:{self.port}")
    
    def stop(self):
        """停止服务"""
        if not self.is_running or not self.server:
            print("服务未运行")
            return
        
        self.server.should_exit = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        self.is_running = False
        print("🛑 服务已停止")
    
    def restart(self):
        """重启服务"""
        print("🔄 重启服务...")
        self.stop()
        self.start()
    
    @property
    def status(self):
        """获取服务状态"""
        return "运行中" if self.is_running else "已停止"
