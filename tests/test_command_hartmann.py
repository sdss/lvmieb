#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from lvmieb.actor import IEBActor


async def test_hartmann_init_and_home(actor: IEBActor, setup_servers):
    hleft = setup_servers["sp1_hartmann_left"]
    hright = setup_servers["sp1_hartmann_right"]

    # initial state with the hartmann doors not initialized
    assert hright.current_status == "closed"
    assert hleft.current_status == "closed"

    # initialize the shutter with hartmann init command
    command = await actor.invoke_mock_command("hartmann init sp1")
    await command
    assert command.status.did_succeed

    assert hright.current_status == "closed"
    assert hleft.current_status == "closed"

    # homing the shutter with hartmann home command
    command = await actor.invoke_mock_command("hartmann home sp1")
    await command
    assert command.status.did_succeed

    assert hright.current_status == "closed"
    assert hleft.current_status == "closed"

    # run the hartmann status command to the actor
    command = await actor.invoke_mock_command("hartmann status sp1")
    await command
    assert command.status.did_succeed

    # check if the virtual hartmann doors are closed
    assert hright.current_status == "closed"
    assert hleft.current_status == "closed"
    assert command.replies[-3].message["sp1_hartmann_left"]["open"] is False
    assert command.replies[-2].message["sp1_hartmann_right"]["open"] is False


async def test_shutter_open_and_close(actor: IEBActor, setup_servers):
    hleft = setup_servers["sp1_hartmann_left"]
    hright = setup_servers["sp1_hartmann_right"]

    # initial state with the hartmann doors not initialized
    assert hright.current_status == "closed"
    assert hleft.current_status == "closed"

    # initialize the shutter with hartmann init command
    command = await actor.invoke_mock_command("hartmann init sp1")
    await command
    assert command.status.did_succeed

    assert hright.current_status == "closed"
    assert hleft.current_status == "closed"

    # open the both hartmann doors
    command = await actor.invoke_mock_command("hartmann open --side=all sp1")
    await command
    assert command.status.did_succeed

    # check the status of the virtual hartmann doors are opened
    assert hright.current_status == "open"
    assert hleft.current_status == "open"
    assert command.replies[-3].message["sp1_hartmann_left"]["open"] is True
    assert command.replies[-2].message["sp1_hartmann_right"]["open"] is True

    # close both of the hartmann doors
    command = await actor.invoke_mock_command("hartmann close --side=all sp1")
    await command
    assert command.status.did_succeed

    # check the status of the virtual hartmann doors are closed
    assert hright.current_status == "closed"
    assert hleft.current_status == "closed"
    assert command.replies[-3].message["sp1_hartmann_left"]["open"] is False
    assert command.replies[-2].message["sp1_hartmann_right"]["open"] is False

    # open left hartmann door
    command = await actor.invoke_mock_command("hartmann open --side=left sp1")
    await command
    assert command.status.did_succeed

    # check the left status
    assert hleft.current_status == "open"
    assert command.replies[-3].message["sp1_hartmann_left"]["open"] is True

    # open right hartmann door
    command = await actor.invoke_mock_command("hartmann open --side=right sp1")
    await command
    assert command.status.did_succeed

    # check the right status
    assert hright.current_status == "open"
    assert command.replies[-2].message["sp1_hartmann_right"]["open"] is True
