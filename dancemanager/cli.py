"""CLI entry point for Dance Manager using Click."""

import click

from dancemanager.classes import classes
from dancemanager.dances import dances
from dancemanager.dancers import dancers
from dancemanager.instructors import instructors
from dancemanager.recital import recital
from dancemanager.teams import teams
from dancemanager.utils import get_store, render_table


@click.group()
@click.version_option(version="1.0.0", prog_name="Dance Manager")
@click.option("--store-path", default=None, help="Path to store JSON file")
@click.pass_context
def cli(ctx, store_path):
    """Dance Manager - CLI for managing a dance studio."""
    ctx.ensure_object(dict)
    ctx.obj["store_path"] = store_path


cli.add_command(classes)
cli.add_command(teams)
cli.add_command(dancers)
cli.add_command(instructors)
cli.add_command(dances)
cli.add_command(recital)


@cli.command()
def migrate():
    """Run all pending database migrations."""
    from dancemanager.migrate import run_migrations
    from dancemanager.store import get_store

    store = get_store()
    run_migrations(store._conn)
    click.echo("Migrations complete.")


@cli.command()
@click.option(
    "--host", default="localhost", help="Host to bind to (default: localhost)"
)
@click.option(
    "--port", default=8000, type=int, help="Port to listen on (default: 8000)"
)
def serve(host, port):
    """Launch the web server."""
    import uvicorn
    from dancemanager.api import create_app

    app = create_app()
    click.echo(f"Starting Dance Manager web server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
