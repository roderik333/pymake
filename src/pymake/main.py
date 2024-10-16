"""A make file replacement."""

import click

from .cmds import bash, build, dump_defaults, manage, play_kube, scaffold
from .interpolate_templates import interpolate_templates, yamlparser, list_templates
from .publish_encode import publish_encode
from .write_templates import podman_scaffold


@click.group(help="General commands")
def cli() -> None:
    pass


@cli.group(help="Podman particular commands")
def podman() -> None:
    pass


cli.add_command(scaffold)
cli.add_command(dump_defaults)
podman.add_command(manage)
podman.add_command(bash)
podman.add_command(build)
podman.add_command(play_kube, "play")
podman.add_command(podman_scaffold, "scaffold")
podman.add_command(yamlparser)
podman.add_command(publish_encode)
podman.add_command(interpolate_templates)
podman.add_command(list_templates)
