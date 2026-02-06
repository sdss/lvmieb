#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from . import parser


if TYPE_CHECKING:
    from lvmieb.actor import ControllersType, IEBCommand


__all__ = ["depth"]


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
    except Exception as err:
        return command.fail(error=err)

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
