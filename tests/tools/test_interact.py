from chattool.tools import InteractiveShell, SimpleAsyncShell
import asyncio
import time

def test_shell_bash():
    # 基础用法
    with InteractiveShell() as shell:
        # 执行多个有状态的命令
        shell.send('cd /tmp')
        shell.send('mkdir -p test_dir')
        shell.send('cd test_dir')
        shell.send('pwd')
        
        # 获取输出
        time.sleep(0.1)  # 等待命令执行
        outputs = shell.get_output()
        for output in outputs:
            print(f">> {output}")

def test_shell_python():
    # 与Python解释器交互
    with InteractiveShell(['python3', '-i']) as py_shell:
        py_shell.send('a = 10')
        py_shell.send('b = 20')
        py_shell.send('print(a + b)')
        
        time.sleep(0.1)
        result = py_shell.get_output()
        print("Python输出:", result)


async def test_shell_async():
    # 基础异步用法
    async with SimpleAsyncShell() as shell:
        # 并发发送多个命令
        await shell.send('echo "Start processing"')
        await shell.send('sleep 1')  # 模拟长时间运行的命令
        await shell.send('echo "Processing complete"')
        
        # 异步获取输出
        outputs = await shell.get_output(timeout=3)
        for output in outputs:
            print(f">> {output}")

# 高级用法：同时管理多个shell
async def test_multi_shell_example():
    # 同时操作多个shell实例
    async def work_with_shell(name, commands):
        async with SimpleAsyncShell() as shell:
            for cmd in commands:
                await shell.send(cmd)
            
            outputs = await shell.get_output(timeout=2)
            print(f"{name} 输出: {outputs}")
    
    # 并发执行
    await asyncio.gather(
        work_with_shell("Shell1", ["echo 'Hello from shell 1'", "pwd"]),
        work_with_shell("Shell2", ["echo 'Hello from shell 2'", "date"]),
        work_with_shell("Shell3", ["echo 'Hello from shell 3'", "whoami"])
    )
