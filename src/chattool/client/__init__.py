import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*")


def main_cli():
    from .main import cli
    cli()


__all__ = [
    "main_cli",
]
