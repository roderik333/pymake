"""Publish and encode secrets."""

import base64
import contextlib
import subprocess
from io import TextIOWrapper

import click
import yaml

__all__ = ["publish_encode"]


@click.command(help="Encode and optionally publish secrets to podman.")
@click.option("-f", "--file", type=click.File("rb"), required=True, help="the secrets template to encode")
@click.option("--publish-secrets", is_flag=True, default=False, help="publish the secrets to the cluster")
def publish_encode(file: TextIOWrapper, publish_secrets=False):
    if file.name.endswith("-secrets-template.yaml"):
        with file as fp:
            data = yaml.safe_load(fp)

        try:
            for key, value in data["data"].items():
                data["data"][key] = base64.b64encode(value.encode()).decode()
        except AttributeError as e:
            click.secho(f"{e}", fg="red", err=True)
            raise SystemExit(1) from AttributeError

        with open(file.name.replace("secrets-template.yaml", "secrets.yaml"), "w") as fp:
            yaml.safe_dump(data, fp)
            click.secho(f"{fp.name.replace('secrets-template.yaml','secrets.yaml')} created", fg="green")

            if publish_secrets:
                click.secho("\nPublishing secrets", fg="blue")
                click.secho("------------------", fg="blue")
                with (
                    subprocess.Popen(
                        [
                            "podman",
                            "kube",
                            "play",
                            "--replace",
                            file.name.replace("secrets-template.yaml", "secrets.yaml"),
                        ],
                        stdout=subprocess.PIPE,
                    ) as proc,
                    contextlib.suppress(AttributeError),
                ):
                    for line in proc.stdout.readlines():  # type: ignore[reportOptionalMemberAccess]
                        line = line.decode().strip("\n")
                        click.secho(f"{line}", fg="green")
                click.secho("------------------", fg="blue")
    else:
        click.secho(f"{file.name} is not a valid template file", fg="red", err=True)
        click.secho(f"{file.name} must be <somename>-secrets-template.yaml", fg="red", err=True)
