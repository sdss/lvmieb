#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-12
# @Filename: test_motor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import pytest

from lvmieb.controller.maskbits import MotorStatus
from lvmieb.controller.motor import MotorController

from ..mockers import MotorMocker, WAGOMocker


async def get_motor_controller(
    current_status: str = "closed",
    motor_type: str = "shutter",
):
    mock_motor = MotorMocker(current_status, motor_type)
    await mock_motor.start()

    return MotorController(
        "sp1",
        motor_type,
        "localhost",
        mock_motor.port,
        wago=WAGOMocker.from_config(),
    )


@pytest.mark.parametrize("motor_type", ["shutter", "hartmann_left", "hartmann_right"])
async def test_motor_get_status(motor_type: str):

    motor_controller = await get_motor_controller(motor_type=motor_type)
    status, bits = await motor_controller.get_status()

    assert status == MotorStatus.POWER_ON | MotorStatus.CLOSED
    assert bits == "10111111" if motor_type == "hartmann_left" else "10111111"


@pytest.mark.parametrize("motor_type", ["shutter", "hartmann_left", "hartmann_right"])
async def test_motor_open(motor_type: str):

    motor_controller = await get_motor_controller(motor_type=motor_type)
    await motor_controller.move(open=True)

    status, _ = await motor_controller.get_status()
    assert status == MotorStatus.POWER_ON | MotorStatus.OPEN
