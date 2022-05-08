#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING

import click

from lvmieb.exceptions import LvmIebError

from . import parser


if TYPE_CHECKING:
    from lvmieb.actor import ControllersType, IEBCommand


@parser.group()
def depth(*args):
    """Controls the linear gauge depth."""
    pass


@depth.command()
@click.option(
    "--camera",
    type=str,
    help="Temporarily sets the camera to which the probes are connected.",
)
async def status(
    command: IEBCommand,
    controllers: ControllersType,
    camera: str | None = None,
):
    """Returns the measurements from the depth probes."""

    depth_gauges = command.actor.depth_gauges
    if depth_gauges is None:
        return command.fail(error="Depth gauge configuration not defined.")

    try:
        depth = await depth_gauges.read()
    except LvmIebError as err:
        return command.fail(error=str(err))

    camera = camera or depth_gauges.camera or "?"
    return command.finish({"depth": {"camera": camera, **depth}})


@depth.command(name="set-camera")
@click.argument("CAMERA", type=str)
async def set_camera(command: IEBCommand, controllers: ControllersType, camera: str):
    """Sets the camera to which the probes are connected."""

    depth_gauges = command.actor.depth_gauges
    if depth_gauges is None:
        return command.fail(error="Depth gauge configuration not defined.")

    depth_gauges.camera = camera

    return command.finish()
