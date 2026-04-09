from chattool.interaction import install_cli_warning_filters

install_cli_warning_filters()


def main_cli():
    from .main import cli

    cli()


def main_pypi_cli():
    import sys

    from .main import cli

    args = sys.argv[1:]
    if not args:
        cli.main(args=["pypi"], prog_name="chatpypi")
        return

    first = args[0]
    known_commands = {"init", "build", "check", "upload", "probe", "--help", "-h"}
    if first not in known_commands and not first.startswith("-"):
        args = ["pypi", "init", *args]
    else:
        args = ["pypi", *args]
    cli.main(args=args, prog_name="chatpypi")


__all__ = [
    "main_cli",
    "main_pypi_cli",
]
