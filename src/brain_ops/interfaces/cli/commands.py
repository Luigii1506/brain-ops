"""Top-level CLI command registration."""

from __future__ import annotations

import typer
from rich.console import Console

from .commands_core import register_core_commands
from .commands_notes import register_note_and_knowledge_commands
from .commands_personal import register_personal_commands
from .commands_projects import register_project_commands
from .commands_scheduling import register_scheduling_commands
from .commands_sources import register_source_commands
from .presenters import print_operations


def register_cli_commands(
    app: typer.Typer,
    console: Console,
    handle_error,
    *,
    version: str,
) -> None:
    register_core_commands(
        app,
        console,
        handle_error,
        version=version,
        print_operations=print_operations,
    )
    register_personal_commands(app, console, handle_error)
    register_note_and_knowledge_commands(app, console, handle_error)
    register_project_commands(app, console, handle_error)
    register_source_commands(app, console, handle_error)
    register_scheduling_commands(app, console, handle_error)

    @app.command("serve-api")
    def serve_api_command(
        host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the API server."),
        port: int = typer.Option(8420, "--port", help="Port to bind the API server."),
    ) -> None:
        """Start the brain-ops REST API server."""
        try:
            from brain_ops.interfaces.api import create_api_app
            import uvicorn
        except ImportError:
            console.print("API dependencies not installed. Run: pip install brain-ops[api]")
            raise typer.Exit(code=1)
        api_app = create_api_app()
        console.print(f"Starting brain-ops API at http://{host}:{port}")
        uvicorn.run(api_app, host=host, port=port)


__all__ = ["register_cli_commands"]
