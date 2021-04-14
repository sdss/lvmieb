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

#when closing multiple shutters asynchronously_CK    
    tasks = []

    for controller_name in controllers:
        tasks.append(controllers[controller_name].send_message("close"))

    command.info(text="Closing all shutters")
    await asyncio.gather(*tasks)
    return command.finish(shutter="close")

#when opening shutters sequently_CK
"""    
    for controller_name in controllers:
        command.info(text=f"Closing the shutter in controller {controller_name}!")
        await controllers[controller_name].send_message("close")
"""
