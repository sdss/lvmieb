# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Mingyeong YANG, Taeeun Kim
# @Date: 2021-03-22
# @Filename: telemetry.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import click

from . import parser


if TYPE_CHECKING:
    from lvmieb.actor.actor import ControllersType, IEBCommand


@parser.group()
def wago(*args):
    """Controls the WAGO IOModule."""
    pass


@wago.command()
@click.argument("SPECTRO", type=click.Choice(["sp1", "sp2", "sp3"]), required=False)
async def status(
    command: IEBCommand,
    controllers: ControllersType,
    spectro: str | None = None,
):
    """Returns the status of WAGO sensors."""

    spectro_list: list[str] = []
    if spectro is None:
        spectro_list = [controller_name for controller_name in controllers]
    else:
        spectro_list = [spectro]

    tasks = []
    for spectro_name in spectro_list:
        if spectro_name not in controllers:
            command.warning(error=f"Spectrograph {spectro!r} is not available.")
            continue

        controller = controllers[spectro_name]
        tasks.append(controller.wago.read_sensors())

    results = await asyncio.gather(*tasks, return_exceptions=True)
    if len(results) == 0:
        return command.fail("No data received.")

    sensors = {}
    for ii, spectro_name in enumerate(spectro_list):
        result = results[ii]
        if isinstance(result, Exception):
            command.warning(f"Failed to read {spectro_name} sensors.")
            continue
        sensors[f"{spectro_name}_sensors"] = result

    return command.finish(**sensors)


@wago.command()
@click.argument("SPECTRO", type=click.Choice(["sp1", "sp2", "sp3"]), required=False)
async def getpower(
    command: IEBCommand,
    controllers: ControllersType,
    spectro: str | None = None,
):
    """Returns the status of the power relays."""

    spectro_list: list[str] = []
    if spectro is None:
        spectro_list = [controller_name for controller_name in controllers]
    else:
        spectro_list = [spectro]

    tasks = []
    for spectro_name in spectro_list:
        if spectro_name not in controllers:
            command.warning(error=f"Spectrograph {spectro!r} is not available.")
            continue

        controller = controllers[spectro_name]
        tasks.append(controller.wago.read_relays())

    results = await asyncio.gather(*tasks, return_exceptions=True)
    if len(results) == 0:
        return command.fail("No data received.")

    relays = {}
    for ii, spectro_name in enumerate(spectro_list):
        result = results[ii]
        if isinstance(result, Exception):
            command.warning(f"Failed to read {spectro_name} relays.")
            continue
        relays[f"{spectro_name}_relays"] = result

    return command.finish(**relays)


@wago.command()
@click.argument(
    "DEVICE",
    type=click.Choice(["shutter", "hartmann_left", "hartmann_right"]),
)
@click.argument("SPECTRO", type=click.Choice(["sp1", "sp2", "sp3"]))
@click.option(
    "--on",
    "action",
    flag_value="ON",
    required=True,
    help="Turn on device",
)
@click.option(
    "--off",
    "action",
    flag_value="OFF",
    required=True,
    help="Turn off device",
)
async def setpower(
    command: IEBCommand,
    controllers: ControllersType,
    device: str,
    action: str,
    spectro: str,
):
    """Switches power on/off to a device."""

    if spectro not in controllers:
        return command.fail(error=f"Spectrograph {spectro!r} is not available.")

    controller = controllers[spectro]

    try:
        closed = True if action == "ON" else False
        await controller.wago.set_relay(device, closed=closed)
    except NameError:
        return command.fail(error=f"Cannot find device {device!r}.")

    await (await command.child_command(f"wago getpower {spectro}"))

    return command.finish()
