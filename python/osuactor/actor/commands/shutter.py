#!/usr/bin/env python                                                                                   
# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Mingyeong Yang, Taeeun Kim
# @Date: 2021-05-12
# @Filename: shutter.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
# added by CK 2021/03/30

from __future__ import annotations

import asyncio
import click
from clu.command import Command

from osuactor.controller.controller import OsuController
from osuactor.exceptions import OsuActorError

from . import parser


__all__ = ["shutter"]


#tasks = []
#connections = []

@parser.group()
def shutter(*args):
    """control the shutter."""

    pass


@shutter.command()
async def connect(command: Command, controllers: dict[str, OsuController]):
    """open the connection with the shutter."""

    connections = []

    for shutter in controllers:
        if controllers[shutter].name == 'shutter':
            try:
                connections.append(controllers[shutter].connect())
            except OsuActorError as err:
                return command.fail(error=str(err))

    command.info(text="Connecting all the shutters")
    await asyncio.gather(*connections)
    return command.finish(shutter = "connected")


@shutter.command()
async def disconnect(command: Command, controllers: dict[str, OsuController]):
    """close the connection with the shutter"""

    connections = []

    for shutter in controllers:
        if controllers[shutter].name == 'shutter':
            try:
                connections.append(controllers[shutter].disconnect())
            except OsuActorError as err:
                return command.fail(error=str(err))

    command.info(text="Disconnecting all the shutters")
    await asyncio.gather(*connections)
    return command.finish(shutter = "disconnected")


@shutter.command()
async def open(command: Command, controllers: dict[str, OsuController]):
    """open the shutter"""

    tasks = []

    for shutter in controllers:
        if controllers[shutter].name == 'shutter':
            try:
                tasks.append(controllers[shutter].send_command("open"))
            except OsuActorError as err:
                return command.fail(error=str(err))


    command.info(text="Opening all shutters")
    await asyncio.gather(*tasks)
    return command.finish(shutter= "open")
    

@shutter.command()
async def close(command: Command, controllers: dict[str, OsuController]):
    """close the shutter"""

    tasks = []

    for shutter in controllers:
        if controllers[shutter].name == 'shutter':
            try:
                tasks.append(controllers[shutter].send_command("close"))
            except OsuActorError as err:
                return command.fail(error=str(err))

    command.info(text="Closing all shutters")
    await asyncio.gather(*tasks)
    return command.finish(shutter= "closed")
   

"""
@shutter.command
async def status(command: Command, controllers: dict[str, OsuController]):
return the status of shutter.

    global connections
    global tasks

    command.info(text="Checking all shutters")
    result_connect = connections
    result_shutter = tasks

    for n in result_connect:
        try:
            if n == "connected":
                command.finish(shutter='connected')
                for m in result_shutter:
                    if m == "open":
                        return command.finish(shutter='open')
                    elif m == "closed":
                        return command.finish(shutter='closed')
                    else:
                        return command.fail(test='shutter is in a bad state')

            elif n == "disconnected":
                return command.finish(shutter='disconnected')

            else:
                return command.fail(text='Shutter is in a bad state')

        except OsuActorError as err:
            return command.fail(error=str(err))
"""

#when opening shutters sequently_CK
"""    
    for controller_name in controllers:
        command.info(text=f"Opening the shutter in controller {controller_name}!")
        await controllers[controller_name].send_message("open")
"""
