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
import re

from clu.command import Command

from osuactor.controller.controller import OsuController
from osuactor.exceptions import OsuActorError

from . import parser

@parser.command()
async def check(command: Command, controllers: dict[str, OsuController]):

#when opening multiple shutters asynchronously_CK    
    tasks = []
    replies = []

    for shutter in controllers:
       if controllers[shutter].name == 'shutter':
            try:
                tasks.append(controllers[shutter].send_command("status"))
            except OsuActorError as err:
                return command.fail(error=str(err))

    command.info(text="Checking all shutters")
    result = await asyncio.gather(*tasks)
    
    for n in result:
        try:
            #shutter_is = n
            #assert isinstance(n, bytes)
            #shutter_status = parse_IS(n)
            if n == "open":
                return command.finish(shutter='open')
            elif n == "closed":
                return command.finish(shutter='closed')
            else:
                command.fail(text='Shutter is in a bad state')
        except OsuActorError as err:
            return command.fail(error=str(err))

"""
def parse_IS(reply: bytes):

    match = re.search(b"\x00\x07IS=([0-1])([0-1])[0-1]{6}\r$", reply)
    if match is None:
        return False

    if match.groups() == (b"1", b"0"):
        return "open"
    elif match.groups() == (b"0", b"1"):
        return "closed"
    else:                                                                                                                                                                             
        return False
"""
