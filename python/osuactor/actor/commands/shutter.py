#!/usr/bin/env python                                                                                   
# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Mingyeong Yang, Taeeun Kim
# @Date: 2021-03-22
# @Filename: actor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
# added by CK 2021/03/30

from __future__ import annotations

import asyncio
import click
from clu.command import Command

from osuactor.controller.controller import OsuController
from osuactor.exceptions import OsuActorError

from . import parser

@click.option(
    "-s",
    "--send",
    type=str,
    default="status",
    help="connect, disconnect, open, close, status",
)   
@parser.command()
async def shutter(command: Command, controllers: dict[str, OsuController], send: str):
    """operate the shutter."""

#when opening multiple shutters asynchronously_CK    
    tasks = []

    for shutter in controllers:
       if controllers[shutter].name == 'shutter':
            try:
                if send == "connect":
                    tasks.append(controllers[shutter].connect())
                elif send == "disconnect":
                    tasks.append(controllers[shutter].disconnect())
                else:
                    tasks.append(controllers[shutter].send_command(send))
            except OsuActorError as err:
                return command.fail(error=str(err))
    if send == "connect":
        command.info(text="Connecting all the shutters")
        await asyncio.gather(*tasks)
        return command.finish(shutter = "connected")
    elif send == "disconnect":
        command.info(text="Disconnecting all the shutters")
        await asyncio.gather(*tasks)
        return command.finish(shutter = "Disconnected")
    elif send == "open":
        command.info(text="Opening all shutters")
        await asyncio.gather(*tasks)
        return command.finish(shutter= "open")
    elif send == "close":
        command.info(text="Closing all shutters")
        await asyncio.gather(*tasks)
        return command.finish(shutter= "closed")
    elif send == "status":
        command.info(text="Checking all shutters")
        result = await asyncio.gather(*tasks)
    
        for n in result:
            try:
                if n == "open":
                    return command.finish(shutter='open')
                elif n == "closed":
                    return command.finish(shutter='closed')
                else:
                    command.fail(text='Shutter is in a bad state')
            except OsuActorError as err:
                return command.fail(error=str(err))


#when opening shutters sequently_CK
"""    
    for controller_name in controllers:
        command.info(text=f"Opening the shutter in controller {controller_name}!")
        await controllers[controller_name].send_message("open")
"""
