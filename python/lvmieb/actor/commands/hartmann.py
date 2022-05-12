# -*- coding: utf-8 -*-
# @Author: Changgon Kim, Mingyeong Yang, Taeeun Kim
# @Date: 2021-05-12
# @Filename: hartmann.py
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


__all__ = ["hartmann"]


@parser.group()
def hartmann(*args):
    """Control the hartmann doors."""

    pass


@hartmann.command()
@click.option(
    "-s",
    "--side",
    type=click.Choice(["all", "right", "left"]),
    default="all",
    help="all, right, or left",
)
@click.argument("spectro", type=click.Choice(["sp1", "sp2", "sp3"]))
async def open(
    command: IEBCommand,
    controllers: ControllersType,
    side: str,
    spectro: str,
):
    """Open the Hartmann doors."""

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    tasks = []
    if side == "all" or side == "left":
        tasks.append(controller.motors["hartmann_left"].move(open=True))
    if side == "all" or side == "right":
        tasks.append(controller.motors["hartmann_right"].move(open=True))

    command.info(text=f"Opening {side} hartmanns")
    try:
        await asyncio.gather(*tasks)
    except MotorControllerError as err:
        return command.fail(error=err)

    await (await command.child_command(f"hartmann status {spectro}"))

    return command.finish()


@hartmann.command()
@click.option(
    "-s",
    "--side",
    type=click.Choice(["all", "right", "left"]),
    default="all",
    help="all, right, or left",
)
@click.argument("spectro", type=click.Choice(["sp1", "sp2", "sp3"]))
async def close(
    command: IEBCommand,
    controllers: ControllersType,
    side: str,
    spectro: str,
):
    """Close the Hartmann doors."""

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    tasks = []
    if side == "all" or side == "left":
        tasks.append(controller.motors["hartmann_left"].move(open=False))
    if side == "all" or side == "right":
        tasks.append(controller.motors["hartmann_right"].move(open=False))

    command.info(text=f"Closing {side} hartmanns")
    try:
        await asyncio.gather(*tasks)
    except MotorControllerError as err:
        return command.fail(error=err)

    await (await command.child_command(f"hartmann status {spectro}"))

    return command.finish()


@hartmann.command()
@click.argument("spectro", type=click.Choice(["sp1", "sp2", "sp3"]))
async def status(command: IEBCommand, controllers: ControllersType, spectro: str):
    """Reports the position of the Hartmann doors."""

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    tasks = []
    tasks.append(controller.motors["hartmann_left"].get_status())
    tasks.append(controller.motors["hartmann_right"].get_status())

    result_hartmann = await asyncio.gather(*tasks)

    hd_status = {}
    for i, name in enumerate(["left", "right"]):
        motor_status, bits = result_hartmann[i]

        power = motor_status & MotorStatus.POWER_ON
        open = motor_status & MotorStatus.OPEN
        invalid = motor_status & (
            MotorStatus.POSITION_INVALID
            | MotorStatus.POSITION_UNKNOWN
            | MotorStatus.POWER_UNKNOWN
        )

        hd_status[name] = {
            "power": power.value > 0,
            "open": open.value > 0,
            "invalid": invalid.value > 0,
            "bits": bits or "?",
        }

    command.info({f"{spectro}_hartmann_left": hd_status["left"]})
    command.info({f"{spectro}_hartmann_right": hd_status["right"]})

    return command.finish()


@hartmann.command()
@click.argument("spectro", type=click.Choice(["sp1", "sp2", "sp3"]))
async def init(command: IEBCommand, controllers: ControllersType, spectro: str):
    """Initialise the hartmanns."""

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    command.info(text="Initializing all hartmanns")

    tasks = []
    for hd in ["hartmann_left", "hartmann_right"]:
        tasks.append(controller.motors[hd].send_command("init"))

    try:
        await asyncio.gather(*tasks)
    except MotorControllerError as err:
        return command.fail(error=err)

    return command.finish()


@hartmann.command()
@click.argument("spectro", type=click.Choice(["sp1", "sp2", "sp3"]))
async def home(command: IEBCommand, controllers: ControllersType, spectro: str):
    """Home the hartmann doors."""

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    command.info(text="Home all hartmanns")

    tasks = []
    for hd in ["hartmann_left", "hartmann_right"]:
        tasks.append(controller.motors[hd].send_command("home"))

    try:
        await asyncio.gather(*tasks)
    except MotorControllerError as err:
        return command.fail(error=err)

    return command.finish()
