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
#from collections.abc import AsyncIterator

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
    def __init__(self, host: str = '10.7.45.27', port: int = 7776, name: str = ""):
        Device.__init__(self, host, port)
        #self.reader, self.writer = await asyncio.open_connection(host, port)
        self.name = name #must use it!!_CK
        self.__status_event = asyncio.Event()


    async def send_message(self, message):
        self.reader, self.writer = await asyncio.open_connection(
        '10.7.45.27', 7776)
        
        c_message = expCmds[message]

        sclHead = chr(0)+chr(7)
        sclTail = chr(13)

        sclStr = sclHead + c_message.upper() + sclTail

        print(f'Send: {message!r}')
        self.writer.write(sclStr.encode())
        await self.writer.drain()

        status, Reply = await self.receive_status(self.reader)
        print('status : ', status)
        print('reply : ', Reply)
        print('Close the connection')
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
                print(sclReply[:4])
                return True, sclReply
            if sclReply[:3] == 'ERR':
                print(sclReply[:3])
                return True, sclReply
            if sclReply[:2] == 'IS':
                print(sclReply[:2])
                return True, sclReply





"""
    async def send_command(self, message: str):
 #       c_message = expCmds[message]
        sclHead = chr(0)+chr(7)
        sclTail = chr(13)
        sclStr = sclHead + message.upper() + sclTail
        self.write(sclStr)
        #await self.drain()

#        status, Reply = await self._listen(self)
#        print('status : ', status)
#        print('reply : ', Reply)
#        return status
"""
"""
    async def receive_status(areader):
        KeepGoing = True
        while KeepGoing:
            sclReply = ""
            data = await areader.read(4096)
            recStr = data.decode()
            sclReply = recStr[2:-1]

            if sclReply[:4] == 'DONE':
                print(sclReply[:4])
                return True, sclReply
            if sclReply[:3] == 'ERR':
                print(sclReply[:3])
                return True, sclReply
            if sclReply[:2] == 'IS':
                print(sclReply[:2])
                return True, sclReply
"""

#async def test():
#    my_device = OsuController()
    #await my_device.start()
    #if my_device.is_connected():
    #    print("connection is open")
    #else:
    #    print("connection is close")

#    result = False
#    await my_device.send_message('open')

 #   if result:
  #      print("shutter open")
   # else:
    #    print("open fail")

    #await my_device.stop()
    #if my_device.is_connected() != True:
    #    print("connection closed")

#asyncio.run(test())



"""
async def send_message(message):
    reader, writer = await asyncio.open_connection(
        '10.7.45.27', 7776)

    sclHead = chr(0)+chr(7)
    sclTail = chr(13)

    sclStr = sclHead + message.upper() + sclTail

    print(f'Send: {message!r}')
    writer.write(sclStr.encode())
    await writer.drain()

    status, Reply = await receive_status(reader)
    print('status : ', status)
    print('reply : ', Reply)
    print('Close the connection')
    writer.close()
    await writer.wait_closed()

async def receive_status(areader):
    KeepGoing = True
    while KeepGoing:
            sclReply = ""
            data = await areader.read(4096)
            recStr = data.decode()
            sclReply = recStr[2:-1]

            if sclReply[:4] == 'DONE':
                print(sclReply[:4])
                return True, sclReply
            if sclReply[:3] == 'ERR':
                print(sclReply[:3])
                return True, sclReply
            if sclReply[:2] == 'IS':
                return True, sclReply
"""
#asyncio.run(send_message('QX4'))



