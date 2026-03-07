from .main import cli as main_cli

import warnings
# Filter specific DeprecationWarning from third-party libraries
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*")

__all__ = [
    "main_cli",
]
