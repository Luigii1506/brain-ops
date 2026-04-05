from __future__ import annotations

from brain_ops import __version__
from brain_ops.interfaces.cli import create_cli_app

app = create_cli_app(version=__version__)


if __name__ == "__main__":
    app()
