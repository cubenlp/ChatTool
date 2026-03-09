import click
from chattool.docker.main import docker_main

@click.command(name="docker")
@click.argument("template", required=False)
@click.argument("output_dir", required=False)
@click.option(
    "--interactive/--no-interactive",
    "-i/-I",
    default=None,
    help="Auto prompt when required args are missing, -i forces interactive, -I disables it.",
)
@click.option("--set", "set_values", multiple=True, help="Override env value, e.g. --set PORT=3100")
@click.option("--compose-name", default="docker-compose.yaml", show_default=True, help="Output compose file name.")
@click.option("--env-name", default=None, help="Output env example file name. Default: <template>.env.example")
@click.option("--force", is_flag=True, help="Overwrite existing files without confirm.")
def docker_cmd(template, output_dir, interactive, set_values, compose_name, env_name, force):
    docker_main(
        template=template,
        output_dir=output_dir,
        interactive=interactive,
        set_values=set_values,
        compose_name=compose_name,
        env_name=env_name,
        force=force,
    )
