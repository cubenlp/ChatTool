from chattool.interaction import install_cli_warning_filters

install_cli_warning_filters()


def main_cli():
    from .main import cli

    cli()


__all__ = [
    "main_cli",
]
