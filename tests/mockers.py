#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-12
# @Filename: mockers.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import os
import re

import drift
from sdsstools import read_yaml_file

from lvmieb.controller.wago import IEBWAGO


async def _read_device(self, *args, **kwargs):

    if self.name in self.module.drift.overrides:
        value = self.module.drift.overrides[self.name]
    else:
        if isinstance(self, drift.Relay):
            value = "closed"
        else:
            value = 0.0

    return (value, None)


async def _open(self, *args, **kwargs):
    self.module.drift.overrides[self.name] = "open"


async def _close(self, *args, **kwargs):
    self.module.drift.overrides[self.name] = "closed"


# Override read() in Device and open/close for relays.
drift.Device.read = _read_device
drift.Relay.open = _open
drift.Relay.close = _close


class WAGOMocker(IEBWAGO):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.overrides = {}

    @classmethod
    def from_config(cls, config_data: str | dict | None = None, **kwargs):

        if config_data is not None:
            return super().from_config(config_data, **kwargs)

        root = os.path.dirname(__file__)
        config_data = read_yaml_file(os.path.join(root, "test_lvmieb.yml")).copy()

        wago_config = config_data["specs"]["sp1"]["wago"]
        wago_config.update({"modules": config_data["wago_modules"]})

        return super().from_config(wago_config, **kwargs)


class MotorMocker:
    """Mocks a hartmann door right that replies to commands with predefined replies."""

    def __init__(self, current_status: str = "closed", motor_type: str = "shutter"):

        self.current_status = current_status
        self.motor_type = motor_type

        self.server = None
        self.port = None

    async def handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:

        while True:
            data = await reader.readuntil(b"\r")
            matched = re.search(b"(QX1|QX2|QX3|QX4|IS)", data)

            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()

                if cmd == "QX3":  # open
                    writer.write(b"\x00\x07%DONE\r")
                    self.current_status = "open"
                elif cmd == "QX4":  # close
                    writer.write(b"\x00\x07%DONE\r")
                    self.current_status = "closed"
                elif cmd == "QX1":  # init
                    writer.write(b"\x00\x07%DONE\r")
                elif cmd == "QX2":  # home
                    writer.write(b"\x00\x07%DONE\r")
                    self.current_status = "open"
                elif cmd == "IS":  # status
                    if (
                        self.motor_type in ["shutter", "hartmann_right"]
                        and self.current_status == "open"
                    ) or (
                        self.motor_type == "hartmann_left"
                        and self.current_status == "closed"
                    ):
                        writer.write(b"\x00\x07IS=10111111\r")
                    else:
                        writer.write(b"\x00\x07IS=01111111\r")
                await writer.drain()

    async def start(self):
        self.server = await asyncio.start_server(self.handle_connection, "localhost", 0)
        await self.server.start_serving()
        self.port = self.server.sockets[0].getsockname()[1]
