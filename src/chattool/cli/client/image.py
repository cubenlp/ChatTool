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
def bing():
    """Bing Image Creator tools."""
    pass

@bing.command(name="generate")
@click.argument("prompt")
def bing_generate(prompt):
    """Generate an image using Bing Image Creator."""
    try:
        generator = create_generator("bing")
        click.echo("Generating image with Bing Image Creator...")
        result = generator.generate(prompt)
        
        if isinstance(result, list):
            click.echo("Generated Images:")
            for item in result:
                click.echo(item)
        else:
            click.echo(f"Result: {result}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == "__main__":
    cli()
