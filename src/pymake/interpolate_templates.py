"""A template parser."""

import pprint
import re
from pathlib import Path
from string import Template
from typing import Any

from yaml import load

from .templates import TEMPLATES

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import click

SIMPLE_REGEX = re.compile(r"\${(.*?)\}")

__all__ = ["yamlparser", "interpolate_templates", "list_templates"]


def read_yaml(yaml_file: Path) -> dict[str, Any]:
    with open(yaml_file, "rb") as fp:
        return load(fp, Loader)


def template_writer(template_innfile: Path, template_outfile: Path, data: dict[str, Any]) -> None:
    with open(template_innfile, "r") as inn_fp:
        template = Template(inn_fp.read())
    with open(template_outfile, "w") as out_fp:
        out_fp.write(template.safe_substitute(data))


def recurse(d: dict[str, Any]) -> dict[str, Any]:
    for key, value in d.items():
        if items := SIMPLE_REGEX.findall(value):
            for i in items:
                if not SIMPLE_REGEX.findall(i):
                    d[key] = value.replace(f"${{{i}}}", d[i])
                    recurse(d)
    return d


def _yamlparser(yaml_file: Path, inn_bound: Path, out_bound: Path) -> None:
    yaml_dict = read_yaml(yaml_file)
    substituted_dict = {key: value for section_dict in yaml_dict.values() for key, value in section_dict.items()}
    substituted_dict = recurse(substituted_dict)
    template_writer(inn_bound, out_bound, substituted_dict)


@click.command("yamlparser", help="Interpolate the yaml configuration template files and write production files.")
@click.option(
    "-f",
    "--yaml-file",
    type=click.Path(exists=True),
    required=True,
    help="Path to the file contaning the substitution variables.",
)
@click.option(
    "-i",
    "--inn-bound",
    type=click.Path(exists=True),
    required=True,
    help="Path to the template where string interpolation will take place.",
)
@click.option(
    "-o",
    "--out-bound",
    type=click.Path(),
    required=True,
    help="The path to where to store the interpolated template.",
)
def yamlparser(yaml_file: Path, inn_bound: Path, out_bound: Path) -> None:
    _yamlparser(yaml_file, inn_bound, out_bound)


@click.command(help="List all the defined templates.")
def list_templates() -> None:
    click.secho("Available templates:", fg="green")
    for template in TEMPLATES:
        click.secho(template["templatefile"], fg="blue")


@click.command(help="Interpolate and write out production yaml files for all the defined templates.")
def interpolate_templates() -> None:
    t = iter(TEMPLATES)
    config = next(t)
    for template in t:
        _yamlparser(
            yaml_file=config["templatefile"], inn_bound=template["templatefile"], out_bound=template["parsedfile"]
        )
