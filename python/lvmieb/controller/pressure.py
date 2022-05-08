#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import re
import warnings
from dataclasses import dataclass

from lvmieb.exceptions import LvmIebUserWarning


__all__ = ["PressureTransducer"]


@dataclass
class PressureTransducer:
    """Communicates with a SENS4 pressure transducer.

    Parameters
    ----------
    spec
        The spectrograph associated with this device.
    camera
        The camera (red, blue, NIR) that this device monitors.
    host
        The host that provides the TCP server.
    port
        The port on which the TCP server is running.
    device_id
        The ID of the device.

    """

    spec: str
    camera: str
    host: str
    port: int
    device_id: int = 254

    async def _read(self, query_string: str = "P"):
        """Queries the transducer."""

        try:
            r, w = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), 1
            )
        except Exception as err:
            warnings.warn(
                f"Transducer {self.camera}: failed connecting to host: {err}",
                LvmIebUserWarning,
            )
            return False

        command = "@" + str(self.device_id) + query_string + "?\\"
        w.write(command.encode())
        await w.drain()

        try:
            reply = await asyncio.wait_for(r.readuntil(b"\\"), 1)
            match = re.search(r"@[0-9]{1,3}ACK([0-9.E+-]+)\\$".encode(), reply)
            if not match:
                raise ValueError("Cannot parse reply.")
            return float(match.groups()[0])
        except Exception as err:
            warnings.warn(
                f"Transducer {self.camera}: query {command!r} failed: {err}",
                LvmIebUserWarning,
            )
            return False
        finally:
            w.close()
            await w.wait_closed()

    async def read_pressure(self):
        """Reads the pressure from the transducer."""

        return await self._read("P")

    async def read_temperature(self):
        """Reads the temperature from the transducer."""

        return await self._read("T")
