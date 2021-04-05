#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2021-01-20
# @Filename: command.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
"""
from __future__ import annotations

import asyncio
import enum
import re
import warnings

from typing import AsyncGenerator, Optional

__all__ = ["OsuCommand", "OsuCommandStatus", "OsuCommandReply"]


class OsuCommandStatus(enum.Enum):
    """"""Status of an OsuController command.""""""

    DONE = enum.auto()
    FAILED = enum.auto()
    RUNNING = enum.auto()
    TIMEDOUT = enum.auto()


class OsuCommand(asyncio.Future):
    """"""Tracks the status and replies to a command sent to the OSU controller.

    ``OsuCommand`` is a `~asyncio.Future` and can be awaited, at which point the
    command will have completed or failed.

    Parameters
    ----------
    command_string
        The command to send to the OSU. Will be converted to uppercase.
    command_id
        The command id to associate with this message.
    controller
        The controller that is running this command.
    expected_replies
        How many replies to expect from the controller before the command is done.
    timeout
        Time without receiving a reply after which the command will be timed out.
        `None` disables the timeout.
    """"""

    def __init__(
        self,
        command_string: str,
        command_id: int,
        controller=None,
        expected_replies: Optional[int] = 1,
        timeout: Optional[float] = None,
    ):
        super().__init__()

        self.command_string = command_string.upper()
        self.command_id = command_id
        self.controller = controller
        self._expected_replies = expected_replies

        #: List of str or bytes: List of replies received for this command.
        self.replies: list[OsuCommandReply] = []

        #: .OsuCommandStatus: The status of the command.
        self.status = OsuCommandStatus.RUNNING

        if self.command_id < 0 or self.command_id > MAX_COMMAND_ID:
            raise ValueError(
                f"command_id must be between 0x00 and 0x{MAX_COMMAND_ID:X}"
            )

class OsuCommandReply:
    """"""A reply received from the Archon to a given command.

    When ``str(Osu_command_reply)`` is called, the reply (without the reply code or
    command id) is returned, except when the reply is binary in which case an error
    is raised.

    Parameters
    ----------
    raw_reply
        The raw reply received from the Archon.
    command
        The command associated with the reply.

    Raise
    -----
    .OsuError
        Raised if the reply cannot be parsed.
    """"""

    def __init__(self, raw_reply: bytes, command: OsuCommand):
        parsed = REPLY_RE.match(raw_reply)
        if not parsed:
            raise OsuError(
                f"Received unparseable reply to command "
                f"{command.raw}: {raw_reply.decode()}"
            )

        self.command = command
        self.raw_reply = raw_reply

        rtype, rcid, rbin, rmessage = parsed.groups()
        self.type: str = rtype.decode()
        self.command_id: int = int(rcid, 16)
        self.is_binary: bool = rbin.decode() == ":"

        self.reply: str | bytes
        if self.is_binary:
            # If the reply is binary, remove the prefixes and save the full
            # content as the reply.
            self.reply = raw_reply.replace(b"<" + rcid + b":", b"")
        else:
            self.reply = rmessage.decode().strip()

    def __str__(self) -> str:
        if isinstance(self.reply, bytes):
            raise OsuError("The reply is binary and cannot be converted to string.")
        return self.reply

    def __repr__(self):
        return f"<OsuCommandReply ({self.raw_reply})>"


        """
