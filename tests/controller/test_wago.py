#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-12
# @Filename: test_wago.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import pytest

from ..mockers import WAGOMocker


@pytest.fixture
def wago():
    yield WAGOMocker.from_config()


async def test_wago(wago: WAGOMocker):

    dev = wago.get_device("shutter")
    assert (await dev.read())[0] == "closed"


async def test_read_sensors(wago: WAGOMocker):

    sensors = await wago.read_sensors()
    for value in sensors.values():
        assert value == 0.0


async def test_read_sensors_with_units(wago: WAGOMocker):

    sensors = await wago.read_sensors(units=True)
    for value in sensors.values():
        assert isinstance(value, tuple)
        assert value[0] == 0.0
        assert value[1] is None


async def test_read_relays(wago: WAGOMocker):

    wago.overrides["shutter"] = "open"

    relays = await wago.read_relays()
    for name, value in relays.items():
        if name == "shutter":
            assert value is False
        else:
            assert value


async def test_open_relay(wago: WAGOMocker):

    relays = await wago.read_relays()
    assert relays["shutter"] is True

    result = await wago.set_relay("shutter", closed=False)
    assert result is True

    relays = await wago.read_relays()
    assert relays["shutter"] is False


async def test_close_relay(wago: WAGOMocker):

    wago.overrides["shutter"] = "open"

    result = await wago.set_relay("shutter", closed=True)
    assert result is True

    relays = await wago.read_relays()
    assert relays["shutter"] is True


async def test_open_relay_already_open(wago: WAGOMocker):

    wago.overrides["shutter"] = "open"

    result = await wago.set_relay("shutter", closed=False)
    assert result is None

    relays = await wago.read_relays()
    assert relays["shutter"] is False


async def test_close_relay_already_closed(wago: WAGOMocker):

    result = await wago.set_relay("shutter", closed=True)
    assert result is None

    relays = await wago.read_relays()
    assert relays["shutter"] is True


async def test_set_relay_bad_name(wago: WAGOMocker):

    with pytest.raises(NameError):
        await wago.set_relay("bad_name")
