"""A make file replacement."""

import click

from .cmds import bash, build, cmd, dump_defaults, play_kube, scaffold


@click.group(help="General commands")
def cli() -> None:
    pass


@cli.group(help="Podman particular commands")
def podman() -> None:
    pass


cli.add_command(scaffold)
cli.add_command(dump_defaults)
cli.add_command(cmd)
cli.add_command(bash)
podman.add_command(build)
podman.add_command(play_kube, "play")
