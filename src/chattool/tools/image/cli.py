import click
from chattool.interaction import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    resolve_command_inputs,
)
from chattool.tools.image import create_generator
from chattool.tools.image.helpers import (
    download_binary,
    echo_model_list,
    resolve_generated_output_path,
    save_binary,
)


PROMPT_SCHEMA = CommandSchema(
    name="image-prompt",
    fields=(CommandField("prompt", prompt="prompt", required=True),),
)


HF_GENERATE_SCHEMA = CommandSchema(
    name="image-huggingface-generate",
    fields=(
        CommandField("prompt", prompt="prompt", required=True),
    ),
)


@click.group(name="image")
def cli():
    """Image generation tools."""
    pass


@cli.group()
def liblib():
    """LiblibAI tools."""
    pass


@liblib.command(name="generate")
@click.argument("prompt", required=False)
@click.option("--model-id", help="Model ID for generation (required).")
@click.option("--output", "-o", help="Optional output file path to download the image.")
@add_interactive_option
def liblib_generate(prompt, model_id, output, interactive):
    """Generate an image using LiblibAI."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chattool image liblib generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        generator = create_generator("liblib")
        click.echo("Generating image with LiblibAI...")

        kwargs = {}
        if model_id:
            kwargs["model_id"] = model_id

        result = generator.generate(prompt, **kwargs)
        click.echo(f"Image URL: {result}")

        if output and result.startswith("http"):
            try:
                download_binary(result, output)
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
            click.echo(
                f"- {model.get('name', 'Unknown')} (ID: {model.get('id', 'Unknown')})"
            )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.group()
def huggingface():
    """Hugging Face tools."""
    pass


@huggingface.command(name="generate")
@click.argument("prompt", required=False)
@click.option(
    "--output",
    "-o",
    required=False,
    help="Optional output file path. Defaults to ./generated/image_huggingface_<model>_<timestamp>.png for bytes results.",
)
@add_interactive_option
def huggingface_generate(prompt, output, interactive):
    """Generate an image using Hugging Face."""
    inputs = resolve_command_inputs(
        schema=HF_GENERATE_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chattool image huggingface generate [PROMPT] [-o PATH] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        from chattool.tools.image.huggingface import HuggingFaceImageGenerator

        generator = create_generator("huggingface")
        click.echo("Generating image with Hugging Face...")
        result = generator.generate(prompt)

        if isinstance(result, bytes):
            output_path = resolve_generated_output_path(
                output,
                provider="huggingface",
                model=HuggingFaceImageGenerator.DEFAULT_MODEL,
            )
            save_binary(result, output_path)
            click.echo(f"Image saved to {output_path}")
        else:
            click.echo(f"Result: {result}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.group()
def tongyi():
    """Tongyi Wanxiang tools."""
    pass


@tongyi.command(name="generate")
@click.argument("prompt", required=False)
@click.option("--style", default="<auto>", help="Image style.")
@click.option("--size", default="1024*1024", help="Image size.")
@click.option("--output", "-o", help="Optional output file path to download the image.")
@add_interactive_option
def tongyi_generate(prompt, style, size, output, interactive):
    """Generate an image using Tongyi Wanxiang."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chattool image tongyi generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        generator = create_generator("tongyi")
        click.echo("Generating image with Tongyi Wanxiang...")
        result = generator.generate(prompt, style=style, size=size)

        # Tongyi returns a list of dicts with 'url'
        if isinstance(result, list):
            for i, item in enumerate(result):
                url = item.get("url")
                click.echo(f"Image {i + 1}: {url}")
                if output and url:
                    download_binary(url, output)
        else:
            click.echo(f"Result: {result}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.group()
def pollinations():
    """Pollinations.ai tools."""
    pass


@pollinations.command(name="generate")
@click.argument("prompt", required=False)
@click.option("--model", help="Model name (flux, turbo, etc).")
@click.option("--width", default=1024, help="Image width.")
@click.option("--height", default=1024, help="Image height.")
@click.option("--output", "-o", help="Optional output file path to download the image.")
@add_interactive_option
def pollinations_generate(prompt, model, width, height, output, interactive):
    """Generate an image using Pollinations.ai."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chattool image pollinations generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

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
                click.echo(f"Downloading to {output}...")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                if PollinationsConfig.POLLINATIONS_API_KEY.value:
                    headers["Authorization"] = (
                        f"Bearer {PollinationsConfig.POLLINATIONS_API_KEY.value}"
                    )

                download_binary(url, output, headers=headers)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@pollinations.command(name="list-models")
def pollinations_list_models():
    """List available image models for Pollinations.ai."""
    try:
        from chattool.tools.image import create_generator

        generator = create_generator("pollinations")
        models = generator.get_models()
        echo_model_list(models, "Available image models for Pollinations.ai:")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.group()
def siliconflow():
    """SiliconFlow tools."""
    pass


@cli.group()
def codex():
    """ChatGPT/Codex OAuth image tools."""
    pass


@siliconflow.command(name="generate")
@click.argument("prompt", required=False)
@click.option("--model", help="Model name.")
@click.option("--size", default="1024x1024", help="Image size (e.g., 1024x1024).")
@click.option("--output", "-o", help="Optional output file path to download the image.")
@add_interactive_option
def siliconflow_generate(prompt, model, size, output, interactive):
    """Generate an image using SiliconFlow API."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chattool image siliconflow generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        from chattool.config import SiliconFlowConfig
        from chattool.tools.image import create_generator

        # Determine model
        model = (
            model
            or SiliconFlowConfig.SILICONFLOW_MODEL_ID.value
            or "black-forest-labs/FLUX.1-schnell"
        )

        generator = create_generator("siliconflow")
        click.echo(f"Generating image with SiliconFlow (model: {model})...")

        result = generator.generate(prompt, model=model, size=size)

        for i, url in enumerate(result):
            click.echo(f"Image URL: {url}")

            if output:
                click.echo(f"Downloading to {output}...")
                download_binary(url, output)

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
            is_image = m.get("type") == "image" or m.get("sub_type") == "text-to-image"
            if is_image:
                image_models.append(m)

        if not image_models:
            image_models = models

        click.echo("Available image models for SiliconFlow:")
        for model in image_models:
            model_id = model.get("id")
            # Check if it's a free model (no Pro/ prefix)
            is_free = not model_id.startswith("Pro/")
            price_info = "FREE" if is_free else "PAID"

            click.echo(f"- {model_id} [{price_info}]")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@codex.command(name="generate")
@click.argument("prompt", required=False)
@click.option(
    "--aspect-ratio",
    type=click.Choice(["square", "landscape", "portrait"]),
    help="Image aspect ratio.",
)
@click.option(
    "--image-model",
    type=click.Choice(
        ["gpt-image-2-low", "gpt-image-2-medium", "gpt-image-2-high"]
    ),
    help="Codex image model preset.",
)
@click.option(
    "--host-model",
    help="Codex host model used to invoke the image_generation tool.",
)
@click.option(
    "--base-url",
    help="Override the Codex backend base URL. The OAuth token is sent to this host.",
)
@click.option(
    "--auth-json",
    help="Optional auth.json path used to resolve the OAuth access token.",
)
@click.option(
    "--timeout",
    type=float,
    help="Request timeout in seconds.",
)
@click.option(
    "--output",
    "-o",
    help="Optional output file path. Defaults to ./generated/image_codex_<model>_<timestamp>.png",
)
@add_interactive_option
def codex_generate(
    prompt,
    aspect_ratio,
    image_model,
    host_model,
    base_url,
    auth_json,
    timeout,
    output,
    interactive,
):
    """Generate an image using the ChatGPT/Codex OAuth image bridge."""
    inputs = resolve_command_inputs(
        schema=PROMPT_SCHEMA,
        provided={"prompt": prompt},
        interactive=interactive,
        usage="Usage: chattool image codex generate [PROMPT] [-i|-I]",
    )
    prompt = inputs["prompt"]

    try:
        generator = create_generator(
            "codex",
            auth_json_path=auth_json,
            base_url=base_url,
            host_model=host_model,
            image_model=image_model,
            aspect_ratio=aspect_ratio,
            timeout_seconds=timeout,
        )
        click.echo(
            "Generating image with Codex "
            f"(host: {generator.host_model}, image: {generator.image_model})..."
        )
        result = generator.generate(prompt)
        output_path = resolve_generated_output_path(
            output,
            provider="codex",
            model=generator.image_model,
            prompt=prompt,
        )
        saved = save_binary(result, output_path)
        click.echo(f"Image saved to {saved}")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@codex.command(name="list-models")
def codex_list_models():
    """List built-in Codex image model presets."""
    try:
        generator = create_generator("codex")
        models = generator.get_models()
        echo_model_list(models, "Available image models for Codex:")
    except Exception as e:
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    cli()
