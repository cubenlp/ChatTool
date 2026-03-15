import os

import click
from rich.console import Console

console = Console()


@click.command(name="svg2gif")
@click.option(
    "-s",
    "--server",
    default=lambda: os.getenv("CHATTOOL_SVG2GIF_SERVER", "http://127.0.0.1:8000"),
    show_default="CHATTOOL_SVG2GIF_SERVER or http://127.0.0.1:8000",
    help="SVG2GIF 服务地址",
)
@click.option("--svg", "svg_path", required=True, help="SVG 文件路径")
@click.option("--gif", "gif_path", default=None, help="GIF 输出路径（可选）")
@click.option("--fps", default=None, type=int, help="GIF 帧率（可选）")
def svg2gif_client(server, svg_path, gif_path, fps):
    """调用 chattool serve svg2gif 将 SVG 转为 GIF"""
    import requests

    payload = {"svg_path": svg_path}
    if gif_path:
        payload["gif_path"] = gif_path
    if fps:
        payload["fps"] = fps

    try:
        with console.status("[bold green]正在转换 SVG..."):
            resp = requests.post(f"{server}/svg2gif", json=payload, timeout=600)
            resp.raise_for_status()
            data = resp.json()
        console.print(f"[bold green]✅ 转换完成[/bold green]")
        console.print(f"GIF: {data.get('gif_path')}")
        console.print(f"Frames: {data.get('frames')}, Duration: {data.get('duration_ms')}ms")
    except requests.RequestException as exc:
        console.print(f"[bold red]❌ 请求失败: {exc}[/bold red]")
        if hasattr(exc, "response") and exc.response is not None:
            console.print(f"服务端响应: {exc.response.text}")
