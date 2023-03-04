#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-13
# @Filename: test_command_depth.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from lvmieb.actor import IEBActor


@pytest.mark.parametrize("camera", [None, "b1"])
async def test_command_depth_status(actor: IEBActor, camera):
    if camera is not None:
        await (await actor.invoke_mock_command(f"depth set-camera {camera}"))

    command = await actor.invoke_mock_command("depth status")
    await command
    assert command.status.did_succeed

    reply = command.replies.get("depth")
    assert isinstance(reply, dict)

    assert reply["camera"] == "?" if camera is None else camera
    assert reply["A"] == 1.5
    assert reply["B"] == 1.5
    assert reply["C"] == 1.5


async def test_command_depth_status_no_gauges(actor: IEBActor):
    actor.depth_gauges = None

    command = await actor.invoke_mock_command("depth status")
    await command
    assert command.status.did_fail


async def test_command_depth_set_camera_no_gauges(actor: IEBActor):
    actor.depth_gauges = None

    command = await actor.invoke_mock_command("depth set-camera b1")
    await command
    assert command.status.did_fail


async def test_command_depth_status_fails_reading(actor: IEBActor, mocker):
    mocker.patch.object(actor.depth_gauges, "read", side_effect=ValueError)

    command = await actor.invoke_mock_command("depth status")
    await command
    assert command.status.did_fail
