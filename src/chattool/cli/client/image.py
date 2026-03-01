import click
from chattool.tools.image import create_generator

@click.group(name="image")
def cli():
    """Image generation tools."""
    pass

@cli.command()
@click.option("--provider", "-p", type=click.Choice(["tongyi", "huggingface", "liblib", "bing"]), required=True, help="Image generation provider.")
@click.argument("prompt")
@click.option("--output", "-o", default="output.png", help="Output file path (for bytes result) or just print URL.")
def generate(provider, prompt, output):
    """Generate an image from text prompt."""
    try:
        generator = create_generator(provider)
        click.echo(f"Generating image with {provider}...")
        result = generator.generate(prompt)
        
        if isinstance(result, bytes):
            with open(output, "wb") as f:
                f.write(result)
            click.echo(f"Image saved to {output}")
        elif isinstance(result, list):
            click.echo("Generated Images:")
            for item in result:
                click.echo(item)
        else:
            click.echo(f"Result: {result}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == "__main__":
    cli()
