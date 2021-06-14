# encoding: utf-8
#
# conftest.py

"""
Here you can add fixtures that will be used for all the tests in this
directory. You can also add conftest.py files in underlying subdirectories.
Those conftest.py will only be applies to the tests in that subdirectory and
underlying directories. See https://docs.pytest.org/en/2.7.3/plugins.html for
more information.
"""


import asyncio
import pytest as pytest
import re

from clu.device import Device

from lvmieb.controller.controller import IebController
from lvmieb.exceptions import (
    LvmIebError,
    LvmIebNotImplemented,
    LvmIebAPIError,
    LvmIebApiAuthError,
    LvmIebMissingDependency,
    LvmIebWarning,
    LvmIebUserWarning,
    LvmIebSkippedTestWarning,
    LvmIebDeprecationWarning,
)

#Exposure shutter commands

expCmds = {"QX1":"init","QX2":"home","QX3":"open","QX4":"close",

           "flash":"QX5","QX8": "on", "QX9":"off","QX10":"ssroff","QX11":"ssron", "IS":"status"}

# Hartmann Door commands

hdCmds = {"QX1":"init","QX2":"home","QX3":"open","QX4":"close","IS":"status"}

@pytest.fixture
async def hartmann_right(request, unused_tcp_port_factory: int):
    """Mocks a 'hartmann door right' that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        initial_status = 'closed'
        status = initial_status
        
        while True:
            data = await reader.readuntil(b'\r')

            matched = re.search(
                b"(QX1|QX2|QX3|QX4|IS)", data
            )

            print(matched)

            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                cmd = hdCmds[cmd]
                print(f"command is now {cmd}!")

                if cmd == "open":
                    status = 'opened'
                elif cmd == "close":
                    status = 'closed'
                
                if cmd == "status":
                    if status == 'opened':
                        writer.write(b'\x00\x07IS=10111111\r')
                    elif status == 'closed':
                        writer.write(b'\x00\x07IS=01111111\r')
                else:
                    print("writer will write ")
                    writer.write(b'\x00\x07%DONE\r')
                await writer.drain()

    port_hart_right = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_hart_right)

    async with server:
        hr = IebController("localhost", port_hart_right, name = "hartmann_right")
        await hr.start()
        yield hr
        await hr.stop()
        server.close()


@pytest.fixture
async def hartmann_left(request, unused_tcp_port_factory: int):
    """Mocks a hartmann door left that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        initial_status = 'closed'
        status = initial_status
        
        while True:
            data = await reader.readuntil(b'\r')

            matched = re.search(
                b"(QX1|QX2|QX3|QX4|IS)", data
            )

            print(matched)

            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                cmd = hdCmds[cmd]
                print(f"command is now {cmd}!")

                if cmd == "open":
                    status = 'opened'
                elif cmd == "close":
                    status = 'closed'
                
                if cmd == "status":
                    if status == 'opened':
                        writer.write(b'\x00\x07IS=10111111\r')
                    elif status == 'closed':
                        writer.write(b'\x00\x07IS=01111111\r')
                else:
                    print("writer will write ")
                    writer.write(b'\x00\x07%DONE\r')
                await writer.drain()

    port_hart_left = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_hart_left)

    async with server:
        hl = IebController("localhost", port_hart_left, name = "hartmann_left")
        await hl.start()
        yield hl
        await hl.stop()
        server.close()


@pytest.fixture
async def shutter(request, unused_tcp_port_factory: int):
    """Mocks a exposure shutter that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        initial_status = 'closed'
        status = initial_status
        
        while True:
            data = await reader.readuntil(b'\r')

            matched = re.search(
                b"(QX1|QX2|QX3|QX4|QX5|QX6|QX8|QX9|QX10|QX11|IS)", data
            )

            print(matched)

            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                cmd = hdCmds[cmd]
                print(f"command is now {cmd}!")

                if cmd == "open":
                    status = 'opened'
                elif cmd == "close":
                    status = 'closed'
                
                if cmd == "status":
                    if status == 'opened':
                        writer.write(b'\x00\x07IS=10111111\r')
                    elif status == 'closed':
                        writer.write(b'\x00\x07IS=01111111\r')
                else:
                    print("writer will write ")
                    writer.write(b'\x00\x07%DONE\r')
                await writer.drain()

    port_shutter = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_shutter)

    async with server:
        sh = IebController("localhost", port_shutter, name = "shutter")
        await sh.start()
        yield sh
        await sh.stop()
        server.close()
