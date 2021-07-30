# -*- coding: utf-8 -*-
# @Author: Changgon Kim, Mingyeong Yang, Taeeun Kim
# @Date: 2021-05-12
# @Filename: hartmann.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
# added by CK 2021/03/30

from __future__ import annotations, print_function, division, absolute_import

import asyncio
import click
from clu.command import Command

from lvmieb.controller.controller import IebController
from lvmieb.exceptions import LvmIebError

from . import parser


__all__ = ["hartmann"]


@parser.group()
def hartmann(*args):
    """control the hartmann door."""

    pass


@hartmann.command()
@click.option(
    "-s",
    "--side",
    type=click.Choice(["all", "right", "left"]),
    default="all",
    help="all, right, or left",
)
async def open(command: Command, controllers: dict[str, IebController], side: str):
    """open the hartmann"""

    tasks = []

    for hartmann in controllers:
        if side == "all" or side == "left":
            if controllers[hartmann].name == 'hartmann_left':
                try:
                    tasks.append(controllers[hartmann].send_command("open"))
                except LvmIebError as err:
                    return command.fail(error=str(err))

        if side == "all" or side == "right":
            if controllers[hartmann].name == 'hartmann_right':
                try:
                    tasks.append(controllers[hartmann].send_command("open"))
                except LvmIebError as err:
                    return command.fail(error=str(err))

    command.info(text=f"Opening {side} hartmanns")
    await asyncio.gather(*tasks)
    if side == "all":
        return command.finish(hartmann_left="opened",
                              hartmann_right="opened")
    elif side == "right":
        return command.finish(hartmann_right="opened")
    elif side == "left":
        return command.finish(hartmann_left="opened")
    command.finish()
    return


@hartmann.command()
@click.option(
    "-s",
    "--side",
    type=click.Choice(["all", "right", "left"]),
    default="all",
    help="all, right, or left",
)
async def close(command: Command, controllers: dict[str, IebController], side: str):
    """close the hartmann"""
    tasks = []

    for hartmann in controllers:
        if side == "all" or side == "right":
            if controllers[hartmann].name == 'hartmann_right':
                try:
                    tasks.append(controllers[hartmann].send_command("close"))
                except LvmIebError as err:
                    return command.fail(error=str(err))

        if side == "all" or side == "left":
            if controllers[hartmann].name == 'hartmann_left':
                try:
                    tasks.append(controllers[hartmann].send_command("close"))
                except LvmIebError as err:
                    return command.fail(error=str(err))

    command.info(text=f"Closing {side} hartmanns")
    await asyncio.gather(*tasks)

    if side == "all":
        return command.finish(hartmann_left="closed",
                              hartmann_right="closed")
    elif side == "right":
        return command.finish(hartmann_right="closed")
    elif side == "left":
        return command.finish(hartmann_left="closed")
    command.finish()
    return


@hartmann.command()
async def status(command: Command, controllers: dict[str, IebController]):
    command.info(text="Checking all hartmanns")
    tasks = []
    print(controllers)
    for h in controllers:
        print(controllers[h].name)
        if controllers[h].name == 'hartmann_right':
            print(controllers[h].name, controllers[h].host, controllers[h].port)
            try:
                tasks.append(controllers[h].get_status())
            except LvmIebError as err:
                return command.fail(error=str(err))
        if controllers[h].name == 'hartmann_left':
            print(controllers[h].name, controllers[h].host, controllers[h].port)
            try:
                tasks.append(controllers[h].get_status())
            except LvmIebError as err:
                return command.fail(error=str(err))
    result_hartmann = await asyncio.gather(*tasks)
    print(result_hartmann)
    try:
        return command.finish(
            hartmann_left=result_hartmann[0],
            hartmann_right=result_hartmann[1]
        )
    except LvmIebError as err:
        return command.fail(error=str(err))
    return command.finish()


@hartmann.command()
async def init(command: Command, controllers: dict[str, IebController]):
    command.info(text="Checking all hartmanns")
    tasks = []
    for h in controllers:
        if controllers[h].name == 'hartmann_right':
            try:
                tasks.append(controllers[h].initialize())
            except LvmIebError as err:
                return command.fail(error=str(err))
        if controllers[h].name == 'hartmann_left':
            try:
                tasks.append(controllers[h].initialize())
            except LvmIebError as err:
                return command.fail(error=str(err))
    await asyncio.gather(*tasks)
    return command.finish()


@hartmann.command()
async def home(command: Command, controllers: dict[str, IebController]):
    command.info(text="Checking all hartmanns")
    tasks = []
    for h in controllers:
        if controllers[h].name == 'hartmann_right':
            try:
                tasks.append(controllers[h].set_home())
            except LvmIebError as err:
                return command.fail(error=str(err))
        if controllers[h].name == 'hartmann_left':
            try:
                tasks.append(controllers[h].set_home())
            except LvmIebError as err:
                return command.fail(error=str(err))
    await asyncio.gather(*tasks)
    return command.finish()
