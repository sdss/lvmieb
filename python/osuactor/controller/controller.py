#added by CK 2021/03/30

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from __future__ import annotations

import asyncio
import configparser
import os
import re
import warnings

from typing import Any, Callable, Iterable, Optional

import numpy
from clu.device import Device

__all__ = ["OsuController"]


# Exposure Shutter Commands:

expCmds = {"init":"QX1","home":"QX2","open":"QX3","close":"QX4",

           "flash":"QX5","inflate":"QX6","deflate":"QX7", "on":"QX8",

           "off":"QX9","ssroff":"QX10","ssron":"QX11", "status":"IS"}


class OsuController(Device):
    #Talks to an Osu controller over TCP/IP.
    def __init__(self, host: str, port: int, name: str = ""):
        Device.__init__(self, host, port)
        self.name = name #must use it!!_CK
        self.__status_event = asyncio.Event()


    async def send_message(self, message, SelectTimeout=0.5):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        
        c_message = expCmds[message]

        sclHead = chr(0)+chr(7)
        sclTail = chr(13)
        sclStr = sclHead + c_message.upper() + sclTail

        self.writer.write(sclStr.encode())
        await self.writer.drain()

        status, Reply = await self.receive_status(self.reader)
        self.writer.close()
        await self.writer.wait_closed()

        return

    async def receive_status(self, areader):
        KeepGoing = True
        while KeepGoing:
            sclReply = ""
            data = await areader.read(4096)
            recStr = data.decode()
            sclReply = recStr[2:-1]

            if sclReply[:4] == 'DONE':
                return True, sclReply
            if sclReply[:3] == 'ERR':
                return True, sclReply
            if sclReply[:2] == 'IS':
                return True, sclReply


