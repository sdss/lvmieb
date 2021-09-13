# -*- coding: utf-8 -*-
# @Author: Changgon Kim, Mingyeong Yang, Taeeun Kim
# @Date: 2021-05-12
# @Filename: hartmann.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
# added by CK 2021/03/30

from __future__ import absolute_import, annotations, division, print_function

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
@click.argument(
    "spectro",
    type=click.Choice(["sp1", "sp2", "sp3"]),
    default="sp1",
    required=False,
)
async def open(
    command: Command, controllers: dict[str, IebController], side: str, spectro: str
):
    """open the hartmann"""

    tasks = []

    for hartmann in controllers:
        if controllers[hartmann].spec == spectro:
            if side == "all" or side == "left":
                if controllers[hartmann].name == "hartmann_left":
                    try:
                        tasks.append(controllers[hartmann].send_command("open"))
                    except LvmIebError as err:
                        return command.fail(error=str(err))

            if side == "all" or side == "right":
                if controllers[hartmann].name == "hartmann_right":
                    try:
                        tasks.append(controllers[hartmann].send_command("open"))
                    except LvmIebError as err:
                        return command.fail(error=str(err))

    command.info(text=f"Opening {side} hartmanns")
    await asyncio.gather(*tasks)
    if side == "all":
        command.info({spectro : {"hartmann_left" : "opened", "hartmann_right" : "opened"}})
    elif side == "right":
        command.info({spectro : {"hartmann_right" : "opened"}})
    elif side == "left":
        command.info({spectro : {"hartmann_left" : "opened"}})
    
    return command.finish()


@hartmann.command()
@click.option(
    "-s",
    "--side",
    type=click.Choice(["all", "right", "left"]),
    default="all",
    help="all, right, or left",
)
@click.argument(
    "spectro",
    type=click.Choice(["sp1", "sp2", "sp3"]),
    default="sp1",
    required=False,
)
async def close(
    command: Command, controllers: dict[str, IebController], side: str, spectro: str
):
    """close the hartmann"""
    tasks = []

    for hartmann in controllers:
        if controllers[hartmann].spec == spectro:
            if side == "all" or side == "right":
                if controllers[hartmann].name == "hartmann_right":
                    try:
                        tasks.append(controllers[hartmann].send_command("close"))
                    except LvmIebError as err:
                        return command.fail(error=str(err))

            if side == "all" or side == "left":
                if controllers[hartmann].name == "hartmann_left":
                    try:
                        tasks.append(controllers[hartmann].send_command("close"))
                    except LvmIebError as err:
                        return command.fail(error=str(err))

    command.info(text=f"Closing {side} hartmanns")
    await asyncio.gather(*tasks)

    if side == "all":
        command.info({spectro : {"hartmann_left" : "closed", "hartmann_right" : "closed"}})
    elif side == "right":
        command.info({spectro : {"hartmann_right" : "closed"}})
    elif side == "left":
        command.info({spectro : {"hartmann_left" : "closed"}})
    
    return command.finish()


@hartmann.command()
@click.argument(
    "spectro",
    type=click.Choice(["sp1", "sp2", "sp3"]),
    default="sp1",
    required=False,
)
async def status(command: Command, controllers: dict[str, IebController], spectro: str):
    command.info(text="Checking all hartmanns")
    tasks = []
    print(controllers)
    for h in controllers:
        print(controllers[h].name)
        if controllers[h].spec == spectro:
            if controllers[h].name == "hartmann_right":
                print(controllers[h].name, controllers[h].host, controllers[h].port)
                try:
                    tasks.append(controllers[h].get_status())
                except LvmIebError as err:
                    return command.fail(error=str(err))
            if controllers[h].name == "hartmann_left":
                print(controllers[h].name, controllers[h].host, controllers[h].port)
                try:
                    tasks.append(controllers[h].get_status())
                except LvmIebError as err:
                    return command.fail(error=str(err))
    result_hartmann = await asyncio.gather(*tasks)
    try:
        command.info({spectro : {
            "hartmann_left" : result_hartmann[0], "hartmann_right" : result_hartmann[1]
            }
                               }
                              )
    except LvmIebError as err:
        return command.fail(error=str(err))
    return command.finish()


@hartmann.command()
@click.argument(
    "spectro",
    type=click.Choice(["sp1", "sp2", "sp3"]),
    default="sp1",
    required=False,
)
async def init(command: Command, controllers: dict[str, IebController], spectro: str):
    command.info(text="Initializing all hartmanns")
    tasks = []
    for h in controllers:
        if controllers[h].spec == spectro:
            if controllers[h].name == "hartmann_right":
                try:
                    tasks.append(controllers[h].initialize())
                except LvmIebError as err:
                    return command.fail(error=str(err))
            if controllers[h].name == "hartmann_left":
                try:
                    tasks.append(controllers[h].initialize())
                except LvmIebError as err:
                    return command.fail(error=str(err))
    await asyncio.gather(*tasks)
    command.info(text= "done")
    return command.finish()


@hartmann.command()
@click.argument(
    "spectro",
    type=click.Choice(["sp1", "sp2", "sp3"]),
    default="sp1",
    required=False,
)
async def home(command: Command, controllers: dict[str, IebController], spectro: str):
    command.info(text="Homing all hartmanns")
    tasks = []
    for h in controllers:
        if controllers[h].spec == spectro:
            if controllers[h].name == "hartmann_right":
                try:
                    tasks.append(controllers[h].set_home())
                except LvmIebError as err:
                    return command.fail(error=str(err))
            if controllers[h].name == "hartmann_left":
                try:
                    tasks.append(controllers[h].set_home())
                except LvmIebError as err:
                    return command.fail(error=str(err))
    await asyncio.gather(*tasks)
    command.info(text= "done")
    return command.finish()
