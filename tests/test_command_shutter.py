#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from lvmieb.actor import IEBActor


async def test_shutter_status(actor: IEBActor, setup_servers):

    shutter = setup_servers["sp1_shutter"]
    shutter.current_status = "open"

    # initialize the shutter with shutter init command
    command = await actor.invoke_mock_command("shutter init sp1")
    await command
    assert command.status.did_succeed

    assert shutter.current_status == "open"

    # run the shutter status command to the actor
    command = await actor.invoke_mock_command("shutter status sp1")
    await command
    assert command.status.did_succeed

    # check if the virtual shutter is closed
    assert shutter.current_status == "open"
    assert command.replies[-1].message["sp1_shutter"]["open"] is True

    # homing the shutter with shutter home command
    command = await actor.invoke_mock_command("shutter home sp1")
    await command
    assert command.status.did_succeed

    assert shutter.current_status == "closed"


async def test_shutter_open_and_close(actor: IEBActor, setup_servers):

    shutter = setup_servers["sp1_shutter"]
    assert shutter.current_status == "closed"

    # initialize the shutter with shutter init command
    command = await actor.invoke_mock_command("shutter init sp1")
    await command
    assert command.status.did_succeed

    assert shutter.current_status == "closed"

    # check the status of the shutter
    command = await actor.invoke_mock_command("shutter status sp1")
    await command
    assert command.status.did_succeed

    assert shutter.current_status == "closed"
    assert command.replies[-1].message["sp1_shutter"]["open"] is False

    # open the closed shutter
    command = await actor.invoke_mock_command("shutter open sp1")
    await command
    assert command.status.did_succeed

    # check the status of the virtual shutter is open
    assert shutter.current_status == "open"
    assert command.replies[-2].message["sp1_shutter"]["open"] is True

    # check again if the status od the virtual shutter is same
    command = await actor.invoke_mock_command("shutter status sp1")
    await command
    assert command.status.did_succeed

    assert shutter.current_status == "open"
    assert command.replies[-1].message["sp1_shutter"]["open"] is True

    # close the open shutter
    command = await actor.invoke_mock_command("shutter close sp1")
    await command
    assert command.status.did_succeed

    # check the status of the virtual shutter is closed
    assert shutter.current_status == "closed"
    assert command.replies[-2].message["sp1_shutter"]["open"] is False
