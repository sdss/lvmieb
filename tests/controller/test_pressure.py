#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-12
# @Filename: test_pressure.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

from lvmieb.controller.pressure import PressureTransducer

from ..mockers import PressureMocker


async def get_pressure_controller():
    mock_transducer = PressureMocker()
    await mock_transducer.start()

    return PressureTransducer("sp1", "b1", "localhost", mock_transducer.port, 253)


async def test_read_pressure():

    pressure_controller = await get_pressure_controller()
    pressure = await pressure_controller.read_pressure()

    assert pressure == 1e-6


async def test_read_temperature():

    pressure_controller = await get_pressure_controller()
    temperature = await pressure_controller.read_temperature()

    assert temperature == 20.0


async def test_read_temperature_connection_fails(mocker):

    mocker.patch("asyncio.open_connection", side_effect=OSError)

    pressure_controller = await get_pressure_controller()
    temperature = await pressure_controller.read_temperature()

    assert temperature is False
