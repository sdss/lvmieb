#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-12
# @Filename: test_motor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio

import pytest

from lvmieb.controller.maskbits import MotorStatus
from lvmieb.controller.motor import MotorController
from lvmieb.exceptions import MotorControllerError

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
async def test_motor_get_status_no_wago(motor_type: str):

    motor_controller = await get_motor_controller(motor_type=motor_type)
    motor_controller.wago = None

    status, bits = await motor_controller.get_status()

    assert status == MotorStatus.POWER_UNKNOWN | MotorStatus.CLOSED
    assert bits == "10111111" if motor_type == "hartmann_left" else "10111111"

    with pytest.raises(RuntimeError):
        await motor_controller.get_power_status()


async def test_motor_get_status_no_power(mocker):

    motor_controller = await get_motor_controller()
    motor_controller.get_power_status = mocker.AsyncMock(return_value=False)

    status, bits = await motor_controller.get_status()
    assert status == MotorStatus.POWER_OFF | MotorStatus.POSITION_UNKNOWN
    assert bits is None


async def test_motor_controller_get_status_send_command_fails(mocker):

    motor_controller = await get_motor_controller()
    motor_controller.send_command = mocker.MagicMock(side_effect=MotorControllerError)

    status, bits = await motor_controller.get_status()
    assert status == MotorStatus.POWER_ON | MotorStatus.POSITION_UNKNOWN
    assert bits is None


async def test_motor_controller_get_status_invalid(mocker):

    motor_controller = await get_motor_controller()
    motor_controller.send_command = mocker.AsyncMock(return_value=b"????")

    status, bits = await motor_controller.get_status()
    assert status == MotorStatus.POWER_ON | MotorStatus.POSITION_INVALID
    assert bits is None


async def test_motor_controller_get_status_parse_invalid(mocker):

    motor_controller = await get_motor_controller()
    mocker.patch("lvmieb.controller.motor.parse_IS", return_value=None)

    status, bits = await motor_controller.get_status()
    assert status == MotorStatus.POWER_ON | MotorStatus.POSITION_INVALID
    assert bits is not None


@pytest.mark.parametrize("motor_type", ["shutter", "hartmann_left", "hartmann_right"])
@pytest.mark.parametrize("open", [True, False, None])
@pytest.mark.parametrize("current_status", ["open", "closed"])
@pytest.mark.parametrize("force", [True, False])
async def test_motor_move(
    motor_type: str,
    open: bool,
    current_status: str,
    force: bool,
    mocker,
):

    motor_controller = await get_motor_controller(
        current_status=current_status,
        motor_type=motor_type,
    )

    assert await motor_controller.move(open=open, force=force)

    status, _ = await motor_controller.get_status()

    if open or (open is None and current_status == "closed"):
        assert status == MotorStatus.POWER_ON | MotorStatus.OPEN
    else:
        assert status == MotorStatus.POWER_ON | MotorStatus.CLOSED


@pytest.mark.parametrize(
    "status",
    [MotorStatus.POSITION_INVALID, MotorStatus.POSITION_UNKNOWN],
)
async def test_motor_move_fails_position_invalid(status: MotorStatus, mocker):

    status |= MotorStatus.POWER_ON

    motor_controller = await get_motor_controller()
    motor_controller.send_command = mocker.AsyncMock(return_value=b"????")

    with pytest.raises(MotorControllerError):
        await motor_controller.move(open=True)


async def test_motor_move_fails_invalid_argument():

    motor_controller = await get_motor_controller()

    with pytest.raises(ValueError):
        await motor_controller.move(open="hello")  # type:ignore


async def test_motor_send_command_connection_error(mocker):

    motor_controller = await get_motor_controller()
    mocker.patch("asyncio.open_connection", side_effect=OSError)

    with pytest.raises(MotorControllerError):
        await motor_controller.send_command("status")


async def test_motor_send_command_connection_timeout(mocker):

    motor_controller = await get_motor_controller()
    mocker.patch("asyncio.wait_for", side_effect=asyncio.TimeoutError)

    with pytest.raises(MotorControllerError):
        await motor_controller.send_command("status")
