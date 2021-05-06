#!/usr/bin/env python                                                                                   
# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Mingyeong Yang, Taeeun Kim
# @Date: 2021-05-06
# @Filename: noconnect.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
# added by MY 2021-05-06

from __future__ import annotations

import asyncio

from clu.command import Command

from osuactor.controller.controller import OsuController
from osuactor.exceptions import OsuActorError

from . import parser

@parser.command()
async def noconnect(command: Command, controllers: dict[str, OsuController]):
    """close the connection"""

    tasks = []

    for shutter in controllers:
       if controllers[shutter].name == 'shutter':
            try:
                tasks.append(controllers[shutter].noconnect())
            except OsuActorError as err:
                return command.fail(error=str(err))

    command.info(text="Close the connection")
    await asyncio.gather(*tasks)
    return command.finish(shutter="no connection")

"""
    for hartman_door_left in controllers:
       if controllers[hartman_door_left].name == 'hart_left':
            try:
                tasks.append(controllers[hartman_door_left].noconnect())
            except OsuActorError as err:
                return command.fail(error=str(err))

    for hartman_door_right in controllers:
       if controllers[hartman_door_right].name == 'hart_right':
            try:
                tasks.append(controllers[hartman_door_right].noconnect())
            except OsuActorError as err:                                                                                                                    
                return command.fail(error=str(err))
"""
