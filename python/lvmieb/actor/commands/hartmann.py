#!/usr/bin/env python                                                                                   
# -*- coding: utf-8 -*-
#
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
    """control the hartmann door right."""

    pass

@hartmann.command()
async def open(command: Command, controllers: dict[str, IebController]):
    """open the hartmann"""

    side = "left"
    tasks = []

    for hartmann in controllers:
        if side == "all" or side == "right":
            if controllers[hartmann].name == 'hartmann_right':
                try:
                    tasks.append(controllers[hartmann].send_command("open"))
                except LvmIebError as err:
                    return command.fail(error=str(err))

        if side == "all" or side == "left":
            if controllers[hartmann].name == 'hartmann_left':
                try:
                    tasks.append(controllers[hartmann].send_command("open"))
                except LvmIebError as err:
                    return command.fail(error=str(err))

    command.info(text="Opening all hartmanns")
    await asyncio.gather(*tasks)
    return command.finish(hartmann= "open")
    

@hartmann.command()
async def close(command: Command, controllers: dict[str, IebController]):
    """close the hartmann"""

    side = "left"
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

    command.info(text="Closing all hartmanns")
    await asyncio.gather(*tasks)
    return command.finish(hartmann= "closed")
   

@hartmann.command()
async def status(command: Command, controllers: dict[str, IebController]):
#return the status of hartmann.

    command.info(text="Checking all hartmanns")
    tasks = []
    print(controllers)
    for h in controllers:
        print(controllers[h].name)
        if controllers[h].name == 'hartmann_left':
            print(controllers[h].name, controllers[h].host, controllers[h].port)
            try:
                tasks.append(controllers[h].get_status())
            except LvmIebError as err:
                return command.fail(error=str(err))
        
    result_hartmann = await asyncio.gather(*tasks)

    for n in result_hartmann:
        try:
            if "open" in n:
                return command.info(
                        status={
                        "open/closed:" : n,
                   }
                )
            elif "closed" in n:
                return command.info(
                        status={
                        "open/closed:" : n,
                   }
                )
            else:
                print(n)
                return command.fail(test='hartmann is in a bad state')
        except LvmIebError as err:
            return command.fail(error=str(err))
        
    return command.finish()
