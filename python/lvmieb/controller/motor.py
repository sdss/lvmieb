#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import re
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from lvmieb.controller.maskbits import MotorStatus
from lvmieb.exceptions import LvmIebUserWarning, MotorControllerError


if TYPE_CHECKING:
    from lvmieb.controller.wago import IEBWAGO


__all__ = ["DEVLIST", "MotorController", "parse_IS"]

# Device list
DEVLIST = ["shutter", "hartmann_left", "hartmann_right"]


# Shutter/HD commands
COMMANDS = {"init": "QX1", "home": "QX2", "open": "QX3", "close": "QX4", "status": "IS"}


@dataclass
class MotorController:
    """Handles a motor controller for the shutter or Hartmann doors.

    Parameters
    ----------
    spec
        The spectrograph with which this motor controller is associated.
    type
        The type of motor controller, one of `.DEVLIST`. Although all motor
        controllers have the same command set, the proximity sensor status
        depends on the type of device.
    host
        The host providing the TCP server.
    port
        The port to the TCP server.
    wago
        Optionally, the `.IEBWAGO` instance associated with this device, used
        to check the power status of the motor controller.

    """

    spec: str
    type: str
    host: str
    port: int
    wago: Optional[IEBWAGO] = None

    TIMEOUT: float = 5

    def __post_init__(self):

        if self.type not in DEVLIST:
            raise ValueError(f"Device type {self.type} is not valid.")

    async def get_power_status(self):
        """Returns the power status of a motor controller."""

        if self.wago is None:
            raise RuntimeError("WAGO module not specified.")

        device = self.wago.get_device(self.type)
        return (await device.read())[0] == "closed"

    async def send_command(self, command: str, timeout: float = 1) -> bytes:
        """Sends a command to the device."""

        if command in COMMANDS:
            command = COMMANDS[command]

        try:
            conn = asyncio.open_connection(self.host, self.port)
            r, w = await asyncio.wait_for(conn, self.TIMEOUT)
        except OSError as err:
            raise MotorControllerError(
                f"{self.type} ({self.spec}): failed connecting to device: {err}"
            )
        except asyncio.TimeoutError:
            raise MotorControllerError(
                f"{self.type} ({self.spec}): timed out connecting to device."
            )

        w.write((f"\00\07{command}\r").encode())
        await w.drain()

        reply = b""
        try:
            while True:
                reply += await asyncio.wait_for(r.readuntil(b"\r"), timeout)
                if command == "IS":
                    return reply
                if b"ERR" in reply or b"DONE" in reply:
                    return reply
        except asyncio.TimeoutError:
            raise MotorControllerError(
                f"{self.type} ({self.spec}): timed out waiting for "
                f"reply to {command!r}.",
            )
        finally:
            w.close()
            await w.wait_closed()

    async def get_status(self) -> tuple[MotorStatus, str | None]:
        """Returns the status and position of the motor.

        This method never raises an error; connection issues or invalid
        states are encoded as `.MotorStatus` bits.

        Returns
        -------
        status
            A tuple in which the first element is a `.MotorController` flag with
            the full status of the motor, and the second is the bytestring returned
            by the ``IS`` command. The second element is null if the command fails.

        """

        motor_status = MotorStatus.POWER_UNKNOWN

        if self.wago is not None:
            power = await self.get_power_status()
            if power is False:
                motor_status = MotorStatus.POWER_OFF | MotorStatus.POSITION_UNKNOWN
                return (motor_status, None)
            else:
                motor_status = MotorStatus.POWER_ON

        try:
            reply = await self.send_command("status")
        except MotorControllerError as err:
            warnings.warn(str(err), LvmIebUserWarning)
            motor_status |= MotorStatus.POSITION_UNKNOWN
            return (motor_status, None)

        match = re.search(b"\x00\x07IS=([0-1]{8})\r$", reply)
        if match is None:
            warnings.warn(
                f"Cannot match reply {reply} for {self.type} in {self.spec}",
                LvmIebUserWarning,
            )
            motor_status |= MotorStatus.POSITION_INVALID
            return (motor_status, None)

        bits = match.group(1).decode()
        status = parse_IS(reply, self.type)

        if status == "open":
            motor_status |= MotorStatus.OPEN
        elif status == "closed":
            motor_status |= MotorStatus.CLOSED
        else:
            motor_status |= MotorStatus.POSITION_INVALID

        return (motor_status, bits)

    async def move(self, open: bool | None = None, force: bool = False) -> bool:
        """Moves the device.

        Parameters
        ----------
        open
            If `True`, opens the device, if `False`, closes it. With `None`,
            switches the position of the device.
        force
            Send the command even if the device is already at the position.

        Returns
        -------
        result
            `True` if the command succeeded or the device is already at the
            position, `False` if it failed.

        """

        status = (await self.get_status())[0]

        if status & (MotorStatus.POSITION_UNKNOWN | MotorStatus.POSITION_INVALID):
            raise MotorControllerError("Motor position is unknown or invalid.")

        if open is None:
            if status & MotorStatus.OPEN:
                command = "close"
            elif status & MotorStatus.CLOSED:
                command = "open"
            else:
                raise ValueError("Invalid motor status.")
        elif open is True:
            command = "open" if (status & MotorStatus.CLOSED or force) else None
        elif open is False:
            command = "close" if (status & MotorStatus.OPEN or force) else None
        else:
            raise ValueError(f"Invalid motor status {open!r}.")

        if command is None:
            return True

        reply = await self.send_command(command, timeout=3.0)

        if b"DONE" in reply:
            return True
        elif b"ERR" in reply:
            return False
        else:
            raise MotorControllerError(
                f"{self.type} ({self.spec}): invalid reply to command {command!r}."
            )


def parse_IS(reply: bytes, device: str):
    """Parses the reply to the shutter IS command."""

    match = re.search(b"\x00\x07IS=([0-1])([0-1])[0-1]{6}\r$", reply)
    if match is None:
        return None

    if match.groups() == (b"1", b"0"):
        if device in ["shutter", "hartmann_right"]:
            return "open"
        else:
            return "closed"
    elif match.groups() == (b"0", b"1"):
        if device in ["shutter", "hartmann_right"]:
            return "closed"
        else:
            return "open"
    else:
        return None
