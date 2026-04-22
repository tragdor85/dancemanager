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
