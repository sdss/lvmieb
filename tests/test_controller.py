#!/usr/bin/env python                                                                                                                                          
# -*- coding: utf-8 -*-
#
# @Author: Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-05-25
# @Filename: test_controller.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio

import pytest
from clu.device import Device

from osuactor.controller.controller import OsuController
from osuactor.exceptions import (
    OsuActorError,
    OsuActorNotImplemented,
    OsuActorAPIError,
    OsuActorApiAuthError,
    OsuActorMissingDependency,
    OsuActorWarning,
    OsuActorUserWarning,
    OsuActorSkippedTestWarning,
    OsuActorDeprecationWarning,
)

@pytest.fixture
async def controller(request, unused_tcp_port: int):
    """Mocks a '.OsuController' that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:

        reader, writer = await open_connection("localhost", unused_tcp_port)

    server = await asyncio.start_server(handle_connection, "localhost", unused_tcp_port)

    async with server:
        osu = OsuController("localhost", unused_tcp_port, name = "test_controller")
        await osu.start()
        yield osu
        await osu.stop()

@pytest.mark.asyncio
async def test_controller(controller: OsuController):
    assert controller.host == "localhost"
#    command = controller.send_command(ping)
#    await command

