#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import re


__all__ = ["DepthGauges"]


class DepthGauges:
    """Reads the value of Heidenhain depth gauges."""

    def __init__(self, host: str, port: int, camera: str | None = None):

        self.host = host
        self.port = port
        self.camera = camera

    async def read(self):
        """Returns the measured values from the depth probes."""

        depth = {"A": -999.0, "B": -999.0, "C": -999.0}

        for channel in depth:
            w = None
            try:
                conn = asyncio.open_connection(self.host, self.port)
                r, w = await asyncio.wait_for(conn, 1)
                w.write(("SEND " + channel + "\n").encode())
                await w.drain()
                reply = await asyncio.wait_for(r.readline(), 1)
            except Exception:
                raise ValueError("Failed retrieving data from depth probes.")
            finally:
                if w is not None:
                    w.close()
                    await w.wait_closed()

            match = re.match(f"\r?{channel} ([+\\-0-9\\.]+) mm".encode(), reply)
            if match:
                depth[channel] = float(match.group(1).decode())
            else:
                raise ValueError(f"Failed parsing depth probe for channel {channel}")

        return depth
