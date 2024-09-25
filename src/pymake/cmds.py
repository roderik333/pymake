"""A collection of commands."""

import contextlib
import json
import pathlib
import subprocess

import click
import yaml

LENGTH = 2

data: dict[str, str] = {}
with contextlib.suppress(FileNotFoundError), open("PyMakeFile.yaml", "r") as fp:
    data = yaml.safe_load(fp)


@click.command(help="Dump the defaults of PyMakeFile.yaml to the terminal.")
def dump_defaults() -> None:
    if data == {}:
        click.secho(
            "No defaults found. Try to run scaffold to create PyMakeFile.yaml with dummy defaults.", fg="red", err=True
        )
    click.secho(json.dumps(data, indent=4), fg="green")


@click.command(help="Scaffold a PyMakeFile.yaml with dummy defaults.")
def scaffold() -> None:
    if pathlib.Path("PyMakeFile.yaml").exists():
        click.secho("PyMakeFile.yaml already exists.", fg="red", err=True)
        return
    with open("PyMakeFile.yaml", "w") as fp:
        _ = yaml.safe_dump(
            {
                "tag": "your-app",
                "containerfile": "ContainerFile",
                "manage": "your-app-root/manage.py",
                "container": "your-pod-your-app",
                "configmaps": ["configmaps/django-env-map-template.yaml", "configmaps/postgres-env-map-template.yaml"],
                "kube": "play-kube.yaml",
            },
            fp,
        )


@click.command(help="Build the application image.")
@click.option(
    "--tag",
    type=str,
    default=data.get("tag", None),
    help="Give the app container a tag. This is the same name as given in your play-kube.yaml",
)
@click.option(
    "--file",
    type=click.Path(),
    default=data.get("containerfile", None),
    help="The path to the Containerfile",
)
def build(tag: str, file: pathlib.Path) -> None:
    _ = subprocess.run(
        [
            "podman",
            "build",
            "--tag",
            f"{tag}",
            "-f",
            f"{file}",
        ]
    )


@click.command(help="Play the Kubernetes configuration.")
@click.option(
    "-k",
    "--kube",
    type=click.Path(),
    default=data.get("kube", None),
    help="The path to the Kubernetes configuration file",
)
@click.option(
    "--configmap",
    type=click.Path(),
    multiple=True,
    default=tuple(data.get("configmaps", [])),
    help="""The path to the configmap files.
    Example:
    pymake podman play --configmap configmaps/django-env-map-template.yaml --configmap configmaps/postgres-env-map-template.yaml""",
)
def play_kube(kube: str, configmap: tuple[str]) -> None:
    """Play the Kubernetes configuration.

    KeyWordArguments:
    configmap (list[pathlib.Path]): The paths to the configmap files.

    Example:
    pymake podman play --kube play-kube.yaml --configmap configmaps/django-env-map-template.yaml --configmap configmaps/postgres-env-map-template.yaml

    """
    if configmap == () or len(configmap) > LENGTH:
        click.secho(
            """
Missing one or more configmaps:""",
            fg="red",
        )
        click.secho(
            """
    Example usage:
    pymake podman play --kube play-kube.yaml --configmap configmaps/django-env-map-template.yaml --configmap configmaps/postgres-env-map-template.yaml

    """,
            fg="green",
        )
    else:
        cmd = [
            "podman",
            "kube",
            "play",
            "--replace",
            f"{kube}",
            *[item for x in configmap for item in ("--configmap", x)],
        ]
        _ = subprocess.run(cmd)


@click.command(help="Run manage.py in the context of the container.")
@click.option(
    "-c",
    "--container",
    default=data.get("container", None),
    type=str,
    help="The name of the container to run manage.py in.",
)
@click.option(
    "-m",
    "--manage-script",
    default=data.get("manage", None),
    type=click.Path(),
    help="The relative path to the manage script in the context of the container.",
)
@click.option("-r", "--run", type=str, help="The django-admin command to run in the context of the container.")
def cmd(container: str, manage_script: str, run: str) -> None:
    try:
        _cmd = run.split(" ")
        _ = subprocess.run(
            [
                "podman",
                "exec",
                "-it",
                f"{container}",
                "python",
                f"{manage_script}",
                *_cmd,
            ],
        )
    except AttributeError:
        click.secho(
            """Please provide a command to execute in the container.
Use the -r/--run option to specify it. For example: pymake cmd -r 'makemigrations your-app-name'""",
            fg="red",
        )


@click.command(help="Enter bash shell in the context of the container.")
@click.option("-c", "--container", default=data.get("container"), type=str, help="The name of the container to enter.")
def bash(container: str | None) -> None:
    if container is None:
        click.secho("You must provide a container.", fg="red", err=True)
    _ = subprocess.run(
        [
            "podman",
            "exec",
            "-it",
            f"{container}",
            "/bin/bash",
        ]
    )
