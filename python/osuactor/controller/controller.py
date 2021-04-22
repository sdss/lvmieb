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

from osuactor.exceptions import OsuActorError, OsuActorWarning
from typing import Any, Callable, Iterable, Optional

import numpy
from clu.device import Device

__all__ = ["OsuController"]


# Device list

devList = ["shutter","hartmann_left","hartmann_right"]


#Exposure shutter commands

expCmds = {"init":"QX1","home":"QX2","open":"QX3","close":"QX4",

           "flash":"QX5","inflate":"QX6","deflate":"QX7", "on":"QX8",

           "off":"QX9","ssroff":"QX10","ssron":"QX11", "status":"IS"}

# Hartmann Door commands

hdCmds = {"init":"QX1","home":"QX2","open":"QX3","close":"QX4","status":"IS"}

class OsuController(Device):
    #Talks to an Osu controller over TCP/IP.
    def __init__(self, host: str, port: int, name: str = ""):
        Device.__init__(self, host, port)
        self.name = name #must use it!!_C

        self.__status_event = asyncio.Event()


    async def send_command(self, command, SelectTimeout= 1):

        #check that the device exists
        if self.name in devList == False:
            raise OsuActorError(f"%s is not a valid device" %self.name)
            return False
        
        #check that the command is legal for the device
        if self.name == "shutter":
            if command in expCmds == False:
                raise OsuActorError(f"%s is not a valid %s command" % (command, self.name))
                return False
            else:
                c_message = expCmds[command]
        elif self.name == "hartmann_left" or self.name == "hartmann_right":
            if command in hdCmds == False:
                raise OsuActorError(f"%s is not a valid %s command" % (command, self.name))
                return False
            else:
                c_message = hdCmds[command]
        else:
            raise OsuActorError(f"%s and %s combination not found" % (command, self.name))
            return False

        #Tweak timeouts
        if self.name == "hartmann_left" or self.name == "hartmann_right":
            if command == "open" or command == "close" or command == "home":
                SelectTimeout = 4.0
        if self.name == "shutter":
            if command == "home":
                SelectTimeout = 4.0

        #connect to the mechanism

        connected = False

        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            connected = True
        except:
            connected = False
            raise OsuActorError(f"Could not connect the %s" %self.name)
            return False

        # parse the low-level command to the hardware
        sclHead = chr(0)+chr(7)
        sclTail = chr(13)
        sclStr = sclHead + c_message.upper() + sclTail
        try:
            self.writer.write(sclStr.encode())
            await self.writer.drain()
        except:
            raise OsuActorError(f"Failed to write the data")
            self.writer.close()
            await self.writer.wait_close()
            return False

        #start the select loop to read the socket
        status, Reply = await self.receive_status(self.reader, SelectTimeout, command)

        self.writer.close()
        await self.writer.wait_closed()

        return True

    async def receive_status(self, areader, timeout, cmd):
        KeepGoing = True
        while KeepGoing:

            sclReply = ""

            if timeout > 0.0:
                try:
                    data = await asyncio.wait_for(areader.read(4096), timeout)
                    recStr = data.decode()
                    sclReply = recStr[2:-1]
                except:
                    self.writer.close()
                    await self.writer.wait_closed()
                    raise OsuActorError(f"Failed to read the data")
                    return False, sclReply
            else:
                raise OsuActorError(f"Wrong timeout!")
                return False, sclReply

            if len(sclReply) > 0:
                if sclReply[:4] == 'DONE':
                    return True, sclReply
                if sclReply[:3] == 'ERR':
                    return True, sclReply
                if sclReply[:2] == 'IS':
                    return True, sclReply

