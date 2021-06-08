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
async def hartmann_right(request, unused_tcp_port: int):
    """Mocks a 'hartmann door right' that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        initial_status = 'close'
        status = initial_status

        while True:
            data = await reader.readuntil(b'\r')
            #data = data.decode()

            #print(data)

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
                    status = 'open'
                elif cmd == "close":
                    status = 'close'
                
                if cmd == "status":
                    if status == 'open':
                        writer.write(b'\x00\x07IS=10111111\r')
                    elif status == 'close':
                        writer.write(b'\x00\x07IS=01111111\r')
                else:
                    print("writer will write ")
                    writer.write(b'\x00\x07%\r')
                await writer.drain()
                writer.close()
                break


    server = await asyncio.start_server(handle_connection, "localhost", unused_tcp_port)

    async with server:
        hr = IebController("localhost", unused_tcp_port, name = "hartmann_right")
        await hr.start()
        yield hr
        await hr.stop()


@pytest.fixture
async def hartmann_left(request, unused_tcp_port: int):
    """Mocks a '.OsuController' that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        reader, writer = await asyncio.open_connection("localhost", unused_tcp_port)

    server = await asyncio.start_server(handle_connection, "localhost", unused_tcp_port)

    async with server:
        hl = IebController("localhost", unused_tcp_port, name = "test_controller")
        await hl.start()
        yield hl
        await hl.stop()

@pytest.fixture
async def shutter(request, unused_tcp_port: int):
    """Mocks a 'hartmann door right' that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        reader, writer = await asyncio.open_connection("localhost", unused_tcp_port)

    server = await asyncio.start_server(handle_connection, "localhost", unused_tcp_port)

    async with server:
        sh = IebController("localhost", unused_tcp_port, name = "shutter")
        await sh.start()
        yield sh
        await sh.stop()

@pytest.fixture
async def wago(request, unused_tcp_port: int):
    """Mocks a 'hartmann door right' that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        reader, writer = await asyncio.open_connection("localhost", unused_tcp_port)

    server = await asyncio.start_server(handle_connection, "localhost", unused_tcp_port)

    async with server:
        wa = IebController("localhost", unused_tcp_port, name = "wago")
        await wa.start()
        yield wa
        await wa.stop()

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