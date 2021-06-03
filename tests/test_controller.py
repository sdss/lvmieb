#!/usr/bin/env python                                                                                                                                          
# -*- coding: utf-8 -*-
#
# @Author: Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-05-25
# @Filename: test_controller.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import pytest as pytest

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
async def controller(request, unused_tcp_port: int):
    """Mocks a '.OsuController' that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:

        reader, writer = await asyncio.open_connection("localhost", unused_tcp_port)

    server = await asyncio.start_server(handle_connection, "localhost", unused_tcp_port)

    async with server:
        ieb = IebController("localhost", unused_tcp_port, name = "test_controller")
        await ieb.start()
        yield ieb
        await ieb.stop()

@pytest.mark.asyncio
async def test_controller(controller: IebController):
    assert controller.host == "localhost"
#    command = controller.send_command(ping)
#    await command

