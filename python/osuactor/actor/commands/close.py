#!/usr/bin/env python                                                                                   
# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Taeeun Kim, Mingyeong YANG
# @Date: 2021-03-22
# @Filename: close.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
#added by CK 2021/03/30

from __future__ import annotations

from clu.command import Command

import asyncio

#from osuactor.controller import controller
from osuactor.controller.controller import OsuController

from osuactor.exceptions import OsuActorError

#from ..tools import check_controller, error_controller, parallel_controllers
from . import parser


@parser.command()
async def close(command: Command, controllers: dict[str, OsuController]):
    """Close the shutter."""

#when closing multiple shutters asynchronously_CK    

    tasks = []

    for shutter in controllers:
        if controllers[shutter].name == 'shutter':
            try:
                tasks.append(controllers[shutter].send_command("close"))
            except OsuActorError as err:
                return command.fail(error=str(err))

    command.info(text="Closing all shutters")
    await asyncio.gather(*tasks)
    return command.finish(shutter="close")


#when opening shutters sequently_CK
"""    
    for controller_name in controllers:
        command.info(text=f"Closing the shutter in controller {controller_name}!")
        await controllers[controller_name].send_message("close")
"""
