import subprocess
import asyncio
import threading
import queue

class InteractiveShell:
    def __init__(self, cmd=['bash']):
        # 创建子进程，重定向所有IO
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,   # 标准输入管道
            stdout=subprocess.PIPE,  # 标准输出管道
            stderr=subprocess.STDOUT, # 错误输出合并到标准输出
            text=True,               # 文本模式
            bufsize=1                # 行缓冲
        )
        
        # 输出队列，用于线程间通信
        self.output_queue = queue.Queue()
        
        # 启动后台线程读取输出
        self.thread = threading.Thread(target=self._read_output)
        self.thread.daemon = True
        self.thread.start()
        self.running = True
    
    def _read_output(self):
        """后台线程：持续读取进程输出"""
        for line in iter(self.proc.stdout.readline, ''):
            if not self.running:
                break
            self.output_queue.put(line.strip())
    
    def send(self, cmd):
        """发送命令到子进程"""
        if self.running and self.proc.poll() is None:
            self.proc.stdin.write(cmd + '\n')
            self.proc.stdin.flush()
    
    def get_output(self, timeout=1):
        """获取输出，支持超时"""
        outputs = []
        try:
            while True:
                line = self.output_queue.get(timeout=timeout)
                outputs.append(line)
        except queue.Empty:
            pass
        return outputs
    
    def shutdown(self, timeout=5):
        """优雅关闭进程"""
        self.running = False
        
        # 尝试优雅退出
        if self.proc.poll() is None:
            try:
                self.proc.stdin.write('exit\n')
                self.proc.stdin.flush()
                self.proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # 强制终止
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
        
        # 清理资源
        if self.thread.is_alive():
            self.thread.join(timeout=2)
        
        if self.proc.stdin:
            self.proc.stdin.close()
        if self.proc.stdout:
            self.proc.stdout.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

class SimpleAsyncShell:
    def __init__(self, cmd=['bash']):
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        self.output_queue = asyncio.Queue()
        self.running = True
        self.read_task = None
    
    async def start(self):
        """启动后台读取任务"""
        self.read_task = asyncio.create_task(self._read_output())
    
    async def _read_output(self):
        """异步读取输出"""
        loop = asyncio.get_event_loop()
        
        while self.running:
            try:
                # 在线程池中执行阻塞的readline操作
                line = await loop.run_in_executor(None, self.proc.stdout.readline)
                if line:
                    await self.output_queue.put(line.strip())
                else:
                    break
            except Exception:
                break
    
    async def send(self, cmd):
        """异步发送命令"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._send_sync, cmd)
    
    def _send_sync(self, cmd):
        """同步发送的内部实现"""
        if self.proc.poll() is None:
            self.proc.stdin.write(cmd + '\n')
            self.proc.stdin.flush()
    
    async def get_output(self, timeout=1):
        """异步获取输出"""
        outputs = []
        try:
            while True:
                # 使用asyncio.wait_for实现超时
                line = await asyncio.wait_for(
                    self.output_queue.get(), 
                    timeout=timeout
                )
                outputs.append(line)
                timeout = 0.1  # 后续行使用更短超时
        except asyncio.TimeoutError:
            pass
        
        return outputs
    
    def get_output_nowait(self):
        """非阻塞获取所有可用输出"""
        outputs = []
        try:
            while True:
                line = self.output_queue.get_nowait()
                outputs.append(line)
        except asyncio.QueueEmpty:
            pass
        return outputs
    
    async def shutdown(self):
        """异步关闭"""
        self.running = False
        
        if self.proc.poll() is None:
            await self.send('exit')
            await asyncio.sleep(0.5)
            
            if self.proc.poll() is None:
                self.proc.terminate()
                await asyncio.sleep(1)
                if self.proc.poll() is None:
                    self.proc.kill()
        
        # 取消后台任务
        if self.read_task:
            self.read_task.cancel()
            try:
                await self.read_task
            except asyncio.CancelledError:
                pass
        
        # 关闭管道
        if self.proc.stdin:
            self.proc.stdin.close()
        if self.proc.stdout:
            self.proc.stdout.close()
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()
