"""Write out templates."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from .templates import PATHS, TEMPLATES, TemplateType

if TYPE_CHECKING:
    from collections.abc import Iterable
    from os import PathLike

__all__ = ["podman_scaffold"]


def create_paths(paths: Iterable[PathLike[str]]) -> None:
    for path in paths:
        if not Path(path).exists():
            Path(path).mkdir(parents=True, exist_ok=True)


def write_templates(templates: list[TemplateType], overwrite: bool) -> None:
    for template in templates:
        if (
            not template["templatefile"].exists() or overwrite
        ):  # Always write the file if it doesn't exist, or overwrite is set.
            template["templatefile"].write_text(template["data"], encoding="utf-8")


@click.command(help="Scaffold the yaml files for a typical django project with dummy values.")
@click.option("--overwrite", is_flag=True, default=False)
def podman_scaffold(overwrite: bool):
    _curdir = Path.cwd()
    create_paths(PATHS.values())
    write_templates(TEMPLATES, overwrite)
