import click
from chattool.tools.image import create_generator

@click.group(name="image")
def cli():
    """Image generation tools."""
    pass

@cli.group()
def liblib():
    """LiblibAI tools."""
    pass

@liblib.command(name="generate")
@click.argument("prompt")
@click.option("--model-id", help="Model ID for generation (required).")
@click.option("--output", "-o", help="Optional output file path to download the image.")
def liblib_generate(prompt, model_id, output):
    """Generate an image using LiblibAI."""
    try:
        generator = create_generator("liblib")
        click.echo("Generating image with LiblibAI...")
        
        kwargs = {}
        if model_id:
            kwargs['model_id'] = model_id
            
        result = generator.generate(prompt, **kwargs)
        click.echo(f"Image URL: {result}")
        
        if output and result.startswith("http"):
            try:
                import requests
                resp = requests.get(result)
                if resp.status_code == 200:
                    with open(output, "wb") as f:
                        f.write(resp.content)
                    click.echo(f"Image saved to {output}")
                else:
                    click.echo(f"Failed to download image: {resp.status_code}")
            except Exception as e:
                click.echo(f"Failed to download image: {e}")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@liblib.command(name="list-models")
def liblib_list_models():
    """List available models for LiblibAI."""
    try:
        generator = create_generator("liblib")
        models = generator.get_models()
        click.echo("Available models for LiblibAI:")
        for model in models:
            click.echo(f"- {model.get('name', 'Unknown')} (ID: {model.get('id', 'Unknown')})")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.group()
def huggingface():
    """Hugging Face tools."""
    pass

@huggingface.command(name="generate")
@click.argument("prompt")
@click.option("--output", "-o", required=True, help="Output file path (required for bytes result).")
def huggingface_generate(prompt, output):
    """Generate an image using Hugging Face."""
    try:
        generator = create_generator("huggingface")
        click.echo("Generating image with Hugging Face...")
        result = generator.generate(prompt)
        
        if isinstance(result, bytes):
            with open(output, "wb") as f:
                f.write(result)
            click.echo(f"Image saved to {output}")
        else:
            click.echo(f"Result: {result}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.group()
def tongyi():
    """Tongyi Wanxiang tools."""
    pass

@tongyi.command(name="generate")
@click.argument("prompt")
@click.option("--style", default="<auto>", help="Image style.")
@click.option("--size", default="1024*1024", help="Image size.")
@click.option("--output", "-o", help="Optional output file path to download the image.")
def tongyi_generate(prompt, style, size, output):
    """Generate an image using Tongyi Wanxiang."""
    try:
        generator = create_generator("tongyi")
        click.echo("Generating image with Tongyi Wanxiang...")
        result = generator.generate(prompt, style=style, size=size)
        
        # Tongyi returns a list of dicts with 'url'
        if isinstance(result, list):
            for i, item in enumerate(result):
                url = item.get('url')
                click.echo(f"Image {i+1}: {url}")
                if output and url:
                    import requests
                    resp = requests.get(url)
                    if resp.status_code == 200:
                        with open(output, "wb") as f:
                            f.write(resp.content)
                        click.echo(f"Image saved to {output}")
        else:
            click.echo(f"Result: {result}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)




@cli.group()
def pollinations():
    """Pollinations.ai tools."""
    pass

@pollinations.command(name="generate")
@click.argument("prompt")
@click.option("--model", help="Model name (flux, turbo, etc).")
@click.option("--width", default=1024, help="Image width.")
@click.option("--height", default=1024, help="Image height.")
@click.option("--output", "-o", help="Optional output file path to download the image.")
def pollinations_generate(prompt, model, width, height, output):
    """Generate an image using Pollinations.ai."""
    try:
        from chattool.config import PollinationsConfig
        from chattool.tools.image import create_generator
        model = model or PollinationsConfig.POLLINATIONS_MODEL_ID.value or "flux"
        generator = create_generator("pollinations", model=model)
        click.echo(f"Generating image with Pollinations.ai (model: {model})...")
        result = generator.generate(prompt, width=width, height=height)
        
        for i, url in enumerate(result):
            click.echo(f"Image URL: {url}")
            
            if output:
                import requests
                click.echo(f"Downloading to {output}...")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                if PollinationsConfig.POLLINATIONS_API_KEY.value:
                    headers["Authorization"] = f"Bearer {PollinationsConfig.POLLINATIONS_API_KEY.value}"
                
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    with open(output, "wb") as f:
                        f.write(resp.content)
                    click.echo(f"Image saved to {output}")
                else:
                    click.echo(f"Failed to download image: {resp.status_code}")
                    if resp.status_code == 401:
                        click.echo("Pollinations 鉴权失败，请检查 POLLINATIONS_API_KEY。")
                    elif resp.status_code == 402:
                        click.echo("Pollinations 余额不足，请检查账户的 Pollen 额度。")
                    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@pollinations.command(name="list-models")
def pollinations_list_models():
    """List available image models for Pollinations.ai."""
    try:
        from chattool.tools.image import create_generator
        generator = create_generator("pollinations")
        models = generator.get_models()
        click.echo("Available image models for Pollinations.ai:")
        for item in models:
            if isinstance(item, dict):
                model_id = item.get("id") or item.get("name") or str(item)
            else:
                model_id = str(item)
            click.echo(f"- {model_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.group()
def siliconflow():
    """SiliconFlow tools."""
    pass

@siliconflow.command(name="generate")
@click.argument("prompt")
@click.option("--model", help="Model name.")
@click.option("--size", default="1024x1024", help="Image size (e.g., 1024x1024).")
@click.option("--output", "-o", help="Optional output file path to download the image.")
def siliconflow_generate(prompt, model, size, output):
    """Generate an image using SiliconFlow API."""
    try:
        from chattool.config import SiliconFlowConfig
        from chattool.tools.image import create_generator
        
        # Determine model
        model = model or SiliconFlowConfig.SILICONFLOW_MODEL_ID.value or "black-forest-labs/FLUX.1-schnell"

        generator = create_generator("siliconflow")
        click.echo(f"Generating image with SiliconFlow (model: {model})...")
        
        result = generator.generate(prompt, model=model, size=size)
        
        for i, url in enumerate(result):
            click.echo(f"Image URL: {url}")
            
            if output:
                import requests
                click.echo(f"Downloading to {output}...")
                resp = requests.get(url)
                if resp.status_code == 200:
                    with open(output, "wb") as f:
                        f.write(resp.content)
                    click.echo(f"Image saved to {output}")
                else:
                    click.echo(f"Failed to download image: {resp.status_code}")
                    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@siliconflow.command(name="list-models")
def siliconflow_list_models():
    """List available image models for SiliconFlow."""
    try:
        from chattool.tools.image import create_generator
        generator = create_generator("siliconflow")
        models = generator.get_models()
        
        # Filter for text-to-image models only if possible
        image_models = []
        for m in models:
            # Check type or sub_type
            is_image = m.get('type') == 'image' or m.get('sub_type') == 'text-to-image'
            if is_image:
                image_models.append(m)
        
        if not image_models:
             image_models = models

        click.echo("Available image models for SiliconFlow:")
        for model in image_models:
            model_id = model.get('id')
            # Check if it's a free model (no Pro/ prefix)
            is_free = not model_id.startswith("Pro/")
            price_info = "FREE" if is_free else "PAID"
            
            click.echo(f"- {model_id} [{price_info}]")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == "__main__":
    cli()
