#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from lvmieb.actor import IEBActor


async def test_actor(actor: IEBActor):

    assert actor


async def test_ping(actor: IEBActor):

    command = await actor.invoke_mock_command("ping")
    await command

    assert command.status.did_succeed
    assert len(command.replies) == 2
    assert command.replies[1].message["text"] == "Pong."
