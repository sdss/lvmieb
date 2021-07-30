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
import re

import pytest as pytest

from lvmieb.controller.controller import IebController


# Exposure shutter commands

expCmds = {"QX1": "init", "QX2": "home", "QX3": "open", "QX4": "close",
           "flash": "QX5", "QX8": "on", "QX9": "off",
           "QX10": "ssroff", "QX11": "ssron", "IS": "status"}

# Hartmann Door commands

hdCmds = {"QX1": "init", "QX2": "home", "QX3": "open", "QX4": "close", "IS": "status"}

hr_status = 'closed'
hl_status = 'closed'
sh_status = 'closed'


@pytest.fixture
async def hartmann_right(request, unused_tcp_port_factory: int):
    """Mocks a 'hartmann door right' that replies to commands with predefined replies."""
    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
    ) -> None:
        global hr_status
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
                    await asyncio.sleep(1.7)
                    hr_status = 'opened'
                    writer.write(b'\x00\x07%DONE\r')
                    assert hr_status == 'opened'
                elif cmd == "close":
                    await asyncio.sleep(1.7)
                    hr_status = 'closed'
                    writer.write(b'\x00\x07%DONE\r')
                    assert hr_status == 'closed'
                elif cmd == "status":
                    if hr_status == 'opened':
                        writer.write(b'\x00\x07IS=10111111\r')
                    elif hr_status == 'closed':
                        writer.write(b'\x00\x07IS=01111111\r')
                await writer.drain()
                print(hr_status)
    port_hart_right = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_hart_right)
    async with server:
        hr = IebController(host="localhost", port=port_hart_right, name='hartmann_right')
        yield hr
    server.close()


@pytest.fixture
async def hartmann_left(request, unused_tcp_port_factory: int):
    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
    ) -> None:
        global hl_status
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
                    await asyncio.sleep(1.7)
                    hl_status = 'opened'
                    writer.write(b'\x00\x07%DONE\r')
                    assert hl_status == 'opened'
                elif cmd == "close":
                    await asyncio.sleep(1.7)
                    hl_status = 'closed'
                    writer.write(b'\x00\x07%DONE\r')
                    assert hl_status == 'closed'
                elif cmd == "status":
                    if hl_status == 'opened':
                        writer.write(b'\x00\x07IS=01111111\r')
                    elif hl_status == 'closed':
                        writer.write(b'\x00\x07IS=10111111\r')
                await writer.drain()
    port_hart_left = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_hart_left)
    async with server:
        hr = IebController("localhost", port_hart_left, name="hartmann_left")
        yield hr
    server.close()


@pytest.fixture
async def shutter(request, unused_tcp_port_factory: int):
    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
    ) -> None:
        global sh_status
        while True:
            data = await reader.readuntil(b'\r')
            matched = re.search(
                b"(QX1|QX2|QX3|QX4|IS)", data
            )
            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                cmd = hdCmds[cmd]

                if cmd == "open":
                    await asyncio.sleep(0.61)
                    sh_status = 'opened'
                    writer.write(b'\x00\x07%DONE\r')
                    assert sh_status == 'opened'
                elif cmd == "close":
                    await asyncio.sleep(0.61)
                    sh_status = 'closed'
                    writer.write(b'\x00\x07%DONE\r')
                    assert sh_status == 'closed'
                elif cmd == "status":
                    if sh_status == 'opened':
                        writer.write(b'\x00\x07IS=10111111\r')
                    elif sh_status == 'closed':
                        writer.write(b'\x00\x07IS=01111111\r')
                await writer.drain()
    port_shutter = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_shutter)
    async with server:
        hr = IebController("localhost", port_shutter, name="shutter")
        yield hr
    server.close()
