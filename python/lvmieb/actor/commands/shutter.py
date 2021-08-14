# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Mingyeong Yang, Taeeun Kim
# @Date: 2021-05-12
# @Filename: shutter.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
# added by CK 2021/03/30

from __future__ import absolute_import, annotations, division, print_function

import asyncio
import datetime

from clu.command import Command

from lvmieb.controller.controller import IebController
from lvmieb.exceptions import LvmIebError

from . import parser


__all__ = ["shutter"]


@parser.group()
def shutter(*args):
    """control the shutter."""

    pass


@shutter.command()
async def open(command: Command, controllers: dict[str, IebController]):
    """open the shutter"""
    tasks = []
    for shutter in controllers:
        if controllers[shutter].spec == "sp1":
            if controllers[shutter].name == "shutter":
                try:
                    tasks.append(controllers[shutter].send_command("open"))
                except LvmIebError as err:
                    return command.fail(error=str(err))
    command.info(text="Opening all shutters")
    print("----open----")
    current_time = datetime.datetime.now()
    print("before command gathered        : %s", current_time)
    await asyncio.gather(*tasks)
    current_time = datetime.datetime.now()
    print("after command gathered         : %s", current_time)
    command.finish(shutter="opened")
    return


@shutter.command()
async def close(command: Command, controllers: dict[str, IebController]):
    """close the shutter"""
    tasks = []
    for shutter in controllers:
        if controllers[shutter].spec == "sp1":
            if controllers[shutter].name == "shutter":
                try:
                    tasks.append(controllers[shutter].send_command("close"))
                except LvmIebError as err:
                    return command.fail(error=str(err))
    command.info(text="Closing all shutters")
    print("----close----")
    current_time = datetime.datetime.now()
    print("before command gathered        : %s", current_time)
    await asyncio.gather(*tasks)
    current_time = datetime.datetime.now()
    print("after command gathered         : %s", current_time)
    command.finish(shutter="closed")
    return


@shutter.command()
async def status(command: Command, controllers: dict[str, IebController]):
    
    command.info(text="Checking all shutters")
    tasks = []

    for shutter in controllers:
        if controllers[shutter].spec == "sp1":
            if controllers[shutter].name == "shutter":
                try:
                    tasks.append(controllers[shutter].send_command("status"))
                except LvmIebError as err:
                    return command.fail(error=str(err))

    result_shutter = await asyncio.gather(*tasks)
    for n in result_shutter:
        try:
            if n == "opened":
                return command.finish(shutter=n)
            elif n == "closed":
                return command.finish(shutter=n)
            else:
                return command.fail(test="shutter is in a bad state")
        except LvmIebError as err:
            return command.fail(error=str(err))
    command.finish()
    return


@shutter.command()
async def init(command: Command, controllers: dict[str, IebController]):
    """initialize the shutter"""
    tasks = []
    for shutter in controllers:
        if controllers[shutter].spec == "sp1":
            if controllers[shutter].name == "shutter":
                try:
                    tasks.append(controllers[shutter].send_command("init"))
                except LvmIebError as err:
                    return command.fail(error=str(err))
    command.info(text="initializing all shutters")
    print("----open----")
    current_time = datetime.datetime.now()
    print("before command gathered        : %s", current_time)
    await asyncio.gather(*tasks)
    current_time = datetime.datetime.now()
    print("after command gathered         : %s", current_time)
    return command.finish()
