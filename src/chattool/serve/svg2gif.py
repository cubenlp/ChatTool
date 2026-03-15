import math
import os
import re
import time
from pathlib import Path
from typing import Optional, Tuple

import click
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="SVG to GIF API",
    description="Convert animated SVGs to GIF via a Selenium WebDriver service.",
    version="1.0.0",
)

config = {
    "chromedriver_url": None,
    "headless": True,
    "fps": 12,
}


class Svg2GifRequest(BaseModel):
    svg_path: str
    gif_path: Optional[str] = None
    fps: Optional[int] = None


def _parse_length(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    match = re.match(r"^\s*([0-9.]+)", value)
    if not match:
        return None
    return float(match.group(1))


def _parse_svg_metadata(svg_path: Path) -> Tuple[int, int, float]:
    content = svg_path.read_text(encoding="utf-8", errors="ignore")

    duration_ms = None
    match = re.search(r"--animation-duration:\s*([0-9.]+)ms", content)
    if not match:
        match = re.search(r"animation-duration:\s*([0-9.]+)ms", content)
    if match:
        duration_ms = float(match.group(1))

    width = height = None
    try:
        import xml.etree.ElementTree as ET

        root = ET.fromstring(content)
        width = _parse_length(root.get("width"))
        height = _parse_length(root.get("height"))
        view_box = root.get("viewBox")
        if view_box:
            parts = [p for p in view_box.strip().split() if p]
            if len(parts) == 4:
                width = width or float(parts[2])
                height = height or float(parts[3])
    except Exception:
        pass

    width = int(width or 1280)
    height = int(height or 720)
    duration_ms = duration_ms or 1000.0
    return width, height, duration_ms


def _resolve_paths(svg_path: str, gif_path: Optional[str]) -> Tuple[Path, Path]:
    svg = Path(svg_path).expanduser()
    if not svg.is_absolute():
        svg = (Path.cwd() / svg).resolve()
    if not svg.exists():
        raise FileNotFoundError(f"SVG not found: {svg}")

    if gif_path:
        gif = Path(gif_path).expanduser()
        if not gif.is_absolute():
            gif = (Path.cwd() / gif).resolve()
    else:
        gif = svg.with_suffix(".gif")

    gif.parent.mkdir(parents=True, exist_ok=True)
    return svg, gif


def _convert_svg_to_gif(
    svg_path: Path,
    gif_path: Path,
    chromedriver_url: str,
    fps: int,
    headless: bool,
) -> Tuple[int, float]:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import imageio.v2 as imageio
    from PIL import Image
    import io

    width, height, duration_ms = _parse_svg_metadata(svg_path)
    duration_sec = duration_ms / 1000.0
    fps = max(1, fps)
    frame_count = max(1, math.ceil(duration_sec * fps))

    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={width + 20},{height + 20}")

    driver = webdriver.Remote(command_executor=chromedriver_url, options=options)
    try:
        driver.get(svg_path.resolve().as_uri())
        driver.execute_script(
            """
            const root = document.documentElement;
            if (root) {
                root.style.margin = '0';
                root.style.background = 'transparent';
            }
            if (document.body) {
                document.body.style.margin = '0';
            }
            """
        )
        wait = WebDriverWait(driver, 10)
        screen_view = wait.until(EC.presence_of_element_located((By.ID, "screen_view")))
        element = wait.until(EC.presence_of_element_located((By.ID, "terminal")))

        frames = []
        for index in range(frame_count):
            t = min(index / fps, max(0.0, duration_sec - 0.001))
            driver.execute_script(
                """
                const el = arguments[0];
                const t = arguments[1];
                const duration = arguments[2];
                el.style.animationPlayState = 'paused';
                el.style.animationDelay = `-${t}s`;
                el.style.animationDuration = `${duration}s`;
                el.style.animationTimingFunction = 'steps(1,end)';
                void el.offsetWidth;
                """,
                screen_view,
                t,
                duration_sec,
            )
            time.sleep(0.02)

            png_bytes = element.screenshot_as_png
            image = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            frames.append(image)

        imageio.mimsave(str(gif_path), frames, duration=1 / fps)
        return frame_count, duration_ms
    finally:
        driver.quit()


@app.post("/svg2gif")
def svg2gif(request: Svg2GifRequest):
    chromedriver_url = config.get("chromedriver_url")
    if not chromedriver_url:
        raise HTTPException(status_code=400, detail="chromedriver_url is not configured.")

    try:
        svg_path, gif_path = _resolve_paths(request.svg_path, request.gif_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    fps = request.fps or config.get("fps") or 12
    try:
        frames, duration_ms = _convert_svg_to_gif(
            svg_path=svg_path,
            gif_path=gif_path,
            chromedriver_url=chromedriver_url,
            fps=fps,
            headless=config.get("headless", True),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "ok": True,
        "gif_path": str(gif_path),
        "frames": frames,
        "duration_ms": duration_ms,
    }


@click.command(name="svg2gif")
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", "-p", default=8000, help="监听端口")
@click.option(
    "--chromedriver-url",
    default=None,
    help="Selenium Chromedriver URL (可通过 CHATTOOL_CHROMEDRIVER_URL 或 BROWSER_SELENIUM_REMOTE_URL 设置)",
)
@click.option("--headless/--no-headless", default=True, help="是否使用无头模式")
@click.option("--fps", default=12, help="GIF 帧率")
def svg2gif_app(host, port, chromedriver_url, headless, fps):
    """
    启动 SVG 转 GIF 服务 (API)
    """
    import uvicorn

    resolved_url = (
        chromedriver_url
        or os.getenv("CHATTOOL_CHROMEDRIVER_URL")
        or os.getenv("BROWSER_SELENIUM_REMOTE_URL")
    )
    config["chromedriver_url"] = resolved_url
    config["headless"] = headless
    config["fps"] = fps

    if not resolved_url:
        click.echo("❌ 未配置 chromedriver URL。请使用 --chromedriver-url 或设置环境变量。")
        raise SystemExit(1)

    click.echo("🚀 启动 SVG 转 GIF 服务")
    click.echo(f"📡 监听: http://{host}:{port}")
    click.echo(f"🔗 Chromedriver: {resolved_url}")
    click.echo(f"🎞️  默认 FPS: {fps}")

    uvicorn.run(app, host=host, port=port)
