#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-13
# @Filename: test_command_wago.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from lvmieb.actor import IEBActor


async def test_command_wago_status(actor: IEBActor):
    command = await actor.invoke_mock_command("wago status")
    await command
    assert command.status.did_succeed

    reply = command.replies.get("sp2_sensors")
    assert reply["rh1"] == 0.0


async def test_command_wago_status_one_fails(actor: IEBActor, mocker):
    mocker.patch.object(
        actor.controllers["sp1"].wago,
        "read_sensors",
        side_effect=OSError,
    )

    command = await actor.invoke_mock_command("wago status")
    await command
    assert command.status.did_succeed

    reply = command.replies.get("sp2_sensors")
    assert reply["rh1"] == 0.0

    with pytest.raises(KeyError):
        command.replies.get("sp1_sensors")

    assert command.replies[-2].message_code == "w"
    assert command.replies[-2].body == {"text": "Failed to read sp1 sensors."}


async def test_command_wago_status_missing_controller(actor: IEBActor):
    actor.controllers.pop("sp2")

    command = await actor.invoke_mock_command("wago status sp2")
    await command
    assert command.status.did_fail


async def test_command_wago_getpower(actor: IEBActor):
    command = await actor.invoke_mock_command("wago getpower")
    await command
    assert command.status.did_succeed

    reply = command.replies.get("sp2_relays")
    assert reply["shutter"] is True


async def test_command_wago_getpower_one_fails(actor: IEBActor, mocker):
    mocker.patch.object(
        actor.controllers["sp1"].wago,
        "read_relays",
        side_effect=OSError,
    )

    command = await actor.invoke_mock_command("wago getpower")
    await command
    assert command.status.did_succeed

    reply = command.replies.get("sp2_relays")
    assert reply["shutter"] is True

    with pytest.raises(KeyError):
        command.replies.get("sp1_relays")

    assert command.replies[-2].message_code == "w"
    assert command.replies[-2].body == {"text": "Failed to read sp1 relays."}


async def test_command_wago_getpower_missing_controller(actor: IEBActor):
    actor.controllers.pop("sp2")

    command = await actor.invoke_mock_command("wago getpower sp2")
    await command
    assert command.status.did_fail


async def test_command_wago_setpower(actor: IEBActor):
    command = await actor.invoke_mock_command("wago setpower --off shutter sp1")
    await command
    assert command.status.did_succeed

    reply = command.replies.get("sp1_relays")
    assert reply["shutter"] is False


async def test_command_wago_setpower_missing_controller(actor: IEBActor):
    actor.controllers.pop("sp2")

    command = await actor.invoke_mock_command("wago setpower --off shutter sp2")
    await command
    assert command.status.did_fail

    assert command.replies[-1].body == {"error": "Spectrograph 'sp2' is not available."}


async def test_command_wago_setpower_bad_device(actor: IEBActor):
    actor.controllers["sp2"].wago.modules["DO"].devices.pop("shutter")

    command = await actor.invoke_mock_command("wago setpower --off shutter sp2")
    await command
    assert command.status.did_fail

    assert command.replies[-1].body == {"error": "Cannot find device 'shutter'."}
