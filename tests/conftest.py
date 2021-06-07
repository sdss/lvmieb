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


@pytest.fixture
async def hartmann_right(request, unused_tcp_port: int):
    """Mocks a 'hartmann door right' that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        reader, writer = await asyncio.open_connection("localhost", unused_tcp_port)

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