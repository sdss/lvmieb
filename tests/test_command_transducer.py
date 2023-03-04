#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-13
# @Filename: test_command_transducer.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from lvmieb.actor import IEBActor


async def test_command_transducer_status(actor: IEBActor):
    command = await actor.invoke_mock_command("transducer status")
    await command
    assert command.status.did_succeed

    reply = command.replies.get("transducer")
    assert isinstance(reply, dict)

    assert reply["r1_temperature"] == 20.0
    assert reply["b2_pressure"] == 1e-6


async def test_command_transducer_fails(actor: IEBActor, mocker):
    mocker.patch.object(
        actor.controllers["sp1"].pressure["b1"],
        "read_pressure",
        side_effect=ValueError,
    )

    command = await actor.invoke_mock_command("transducer status sp1")
    await command
    assert command.status.did_succeed

    reply = command.replies.get("transducer")

    assert reply["r1_temperature"] == 20.0
    assert reply["b1_pressure"] == -999.0
