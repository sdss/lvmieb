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
async def connect(command: Command, controllers: dict[str, IebController]):
    """open the connection with all of the hartmann door left, and right simultaneously."""

    connections = []

    for hartmann in controllers:
        if controllers[hartmann].name == 'hartman_right':
            try:
                connections.append(controllers[hartmann].connect())
            except LvmIebError as err:
                return command.fail(error=str(err))
            
        if controllers[hartmann].name == 'hartman_left':
            try:
                connections.append(controllers[hartmann].connect())
            except LvmIebError as err:
                return command.fail(error=str(err))

    command.info(text="Connecting all the hartmann doors")
    await asyncio.gather(*connections)
    return command.finish(hartmann = "connected")


@hartmann.command()
async def disconnect(command: Command, controllers: dict[str, IebController]):
    """close the connection with all of the hartmann door left, and right simultaneously"""

    connections = []

    for hartmann in controllers:
        if controllers[hartmann].name == 'hartman_right':
            try:
                connections.append(controllers[hartmann].disconnect())
            except LvmIebError as err:
                return command.fail(error=str(err))
            
        if controllers[hartmann].name == 'hartman_left':
            try:
                connections.append(controllers[hartmann].disconnect())
            except LvmIebError as err:
                return command.fail(error=str(err))

    command.info(text="Disconnecting all the hartmann doors")
    await asyncio.gather(*connections)
    return command.finish(hartmann = "disconnected")


@hartmann.command()
@click.option(
    "-s",
    "--side",
    type=click.Choice(["all", "right", "left"]),
    default = "all",
    help="all, right, or left",
)
async def open(command: Command, side: str, controllers: dict[str, IebController]):
    """open the hartmann"""

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
@click.option(
    "-s",
    "--side",
    type=click.Choice(["all", "right", "left"]),
    default = "all",
    help="all, right, or left",
)
async def close(command: Command, side: str, controllers: dict[str, IebController]):
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

    command.info(text="Closing all hartmanns")
    await asyncio.gather(*tasks)
    return command.finish(hartmann= "closed")
   

@hartmann.command()
async def status(command: Command, controllers: dict[str, IebController]):
#return the status of hartmann.

    command.info(text="Checking all hartmanns")
    tasks = []
    connection = []

    for hartmann in controllers:
        if controllers[hartmann].name == 'hartmann_right':
            try:
                tasks.append(controllers[hartmann].send_command("status"))
                connection.append(controllers[hartmann].connected)
            except LvmIebError as err:
                return command.fail(error=str(err))

        if controllers[hartmann].name == 'hartmann_left':
            try:
                tasks.append(controllers[hartmann].send_command("status"))
                connection.append(controllers[hartmann].connected)
            except LvmIebError as err:
                return command.fail(error=str(err))
        
    result_hartmann = await asyncio.gather(*tasks)

    for n in result_hartmann:
        try:
            if "open" in n:
                return command.info(
                        status={
                        "open/closed:" : n,
                        "connected/disconnected" : connection[result_hartmann.index(n)]
                    }
                )
            elif "closed" in n:
                return command.info(
                        status={
                        "open/closed:" : n,
                        "connection/disconnected" : connection[result_hartmann.index(n)]
                    }
                )
            else:
                return command.fail(test='hartmann is in a bad state')
        except LvmIebError as err:
            return command.fail(error=str(err))


"""
    for m in result_connected:
        for n in result_hartmann:
            try:
                if n == "open":
                    return command.finish(
                        status={
                        "open/closed:" : n,
                        "connected/disconnected:" : m
                    }
                )
                elif n == "closed":
                    return command.finish(
                        status={
                        "open/closed:" : n,
                        "connected/disconnected:" : m
                    }
                )
                else:
                    return command.fail(test='hartmann is in a bad state')
            except LvmIebError as err:
                return command.fail(error=str(err))
"""

#when opening hartmanns sequently_CK
"""    
    for controller_name in controllers:
        command.info(text=f"Opening the hartmann in controller {controller_name}!")
        await controllers[controller_name].send_message("open")
"""
