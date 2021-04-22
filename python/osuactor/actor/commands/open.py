#added by CK 2021/03/30
from __future__ import annotations

import asyncio

from clu.command import Command

from osuactor.controller.controller import OsuController
from osuactor.exceptions import OsuActorError

from . import parser

@parser.command()
async def open(command: Command, controllers: dict[str, OsuController]):

#when opening multiple shutters asynchronously_CK    
    tasks = []

    for shutter in controllers:
       if controllers[shutter].name == 'shutter':
            try:
                tasks.append(controllers[shutter].send_command("open"))
            except OsuActorError as err:
                return command.fail(error=str(err))

    command.info(text="Opening all shutters")
    await asyncio.gather(*tasks)
    return command.finish(shutter="open")

#when opening shutters sequently_CK
"""    
    for controller_name in controllers:
        command.info(text=f"Opening the shutter in controller {controller_name}!")
        await controllers[controller_name].send_message("open")
"""
