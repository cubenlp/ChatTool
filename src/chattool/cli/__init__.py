import warnings
# Filter specific DeprecationWarning from third-party libraries
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*")

def main_cli():
    from .main import cli
    cli()

__all__ = [
    "main_cli",
]
