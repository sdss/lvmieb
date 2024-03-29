# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Mingyeong Yang, Taeeun Kim
# @Date: 2021-05-12
# @Filename: shutter.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
# added by CK 2021/03/30

from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING

import click

from lvmieb.controller.maskbits import MotorStatus
from lvmieb.exceptions import MotorControllerError

from . import parser


if TYPE_CHECKING:
    from lvmieb.actor import ControllersType, IEBCommand


__all__ = ["shutter"]


@parser.group()
def shutter(*args):
    """Control the shutter."""

    pass


@shutter.command()
@click.argument("spectro", type=str, required=False)
async def open(
    command: IEBCommand,
    controllers: ControllersType,
    spectro: str | None = None,
):
    """Open the shutter."""

    if spectro is None:
        if len(controllers) > 1:
            return command.fail("Multiple controllers present, SPECTRO is required.")
        spectro = list(controllers.keys())[0]

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    tasks = []
    tasks.append(controller.motors["shutter"].move(open=True))

    command.info(text="Opening shutter")
    try:
        await asyncio.gather(*tasks)
    except MotorControllerError as err:
        return command.fail(error=err)

    await (await command.child_command(f"shutter status {spectro}"))

    return command.finish()


@shutter.command()
@click.argument("spectro", type=str, required=False)
async def close(
    command: IEBCommand,
    controllers: ControllersType,
    spectro: str | None = None,
):
    """Close the shutter."""

    if spectro is None:
        if len(controllers) > 1:
            return command.fail("Multiple controllers present, SPECTRO is required.")
        spectro = list(controllers.keys())[0]

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    tasks = []
    tasks.append(controller.motors["shutter"].move(open=False))

    command.info(text="Closing shutter")
    try:
        await asyncio.gather(*tasks)
    except MotorControllerError as err:
        return command.fail(error=err)

    await (await command.child_command(f"shutter status {spectro}"))

    return command.finish()


@shutter.command()
@click.argument("spectro", type=str, required=False)
async def status(
    command: IEBCommand,
    controllers: ControllersType,
    spectro: str | None = None,
):
    """Reports the position of the shutter."""

    if spectro is None:
        if len(controllers) > 1:
            return command.fail("Multiple controllers present, SPECTRO is required.")
        spectro = list(controllers.keys())[0]

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    tasks = []
    tasks.append(controller.motors["shutter"].get_status())

    result_shutter = await asyncio.gather(*tasks)

    shutter_status = {}
    motor_status, bits = result_shutter[0]

    power = motor_status & MotorStatus.POWER_ON
    open = motor_status & MotorStatus.OPEN
    invalid = motor_status & (
        MotorStatus.POSITION_INVALID
        | MotorStatus.POSITION_UNKNOWN
        | MotorStatus.POWER_UNKNOWN
    )

    shutter_status = {
        "power": power.value > 0,
        "open": open.value > 0,
        "invalid": invalid.value > 0,
        "bits": bits or "?",
    }

    return command.finish({f"{spectro}_shutter": shutter_status})


@shutter.command()
@click.argument("spectro", type=str, required=False)
async def init(
    command: IEBCommand,
    controllers: ControllersType,
    spectro: str | None = None,
):
    """Initialise the shutter."""

    if spectro is None:
        if len(controllers) > 1:
            return command.fail("Multiple controllers present, SPECTRO is required.")
        spectro = list(controllers.keys())[0]

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    command.info(text="Initializing shutter")

    tasks = []
    tasks.append(controller.motors["shutter"].send_command("init"))

    try:
        await asyncio.gather(*tasks)
    except MotorControllerError as err:
        return command.fail(error=err)

    return command.finish()


@shutter.command()
@click.argument("spectro", type=str, required=False)
async def home(
    command: IEBCommand,
    controllers: ControllersType,
    spectro: str | None = None,
):
    """Home the shutter."""

    if spectro is None:
        if len(controllers) > 1:
            return command.fail("Multiple controllers present, SPECTRO is required.")
        spectro = list(controllers.keys())[0]

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    command.info(text="Homing shutter")

    tasks = []
    tasks.append(controller.motors["shutter"].send_command("home"))

    try:
        await asyncio.gather(*tasks)
    except MotorControllerError as err:
        return command.fail(error=err)

    return command.finish()
