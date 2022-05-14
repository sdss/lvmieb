#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import pathlib

import pytest

import clu.testing
from sdsstools import read_yaml_file

from lvmieb.actor import IEBActor
from lvmieb.controller import IEBController

from .mockers import MotorMocker, PressureMocker, WAGOMocker


@pytest.fixture
def config():

    config_file = pathlib.Path(__file__).parent / "./test_lvmieb.yml"
    yield read_yaml_file(str(config_file))


@pytest.fixture
async def setup_servers(config, mocker):

    mocker.patch("lvmieb.controller.controller.IEBWAGO", WAGOMocker)

    servers = []
    for spec_name, spec_config in config["specs"].items():
        for motor_type, motor_config in spec_config["motor_controllers"].items():
            motor_mocker = MotorMocker(spec_name, motor_type=motor_type)
            await motor_mocker.start()
            motor_config["host"] = "localhost"
            motor_config["port"] = motor_mocker.port
            servers.append(motor_mocker)
        for camera, pressure_config in spec_config["pressure"].items():
            pressure_mocker = PressureMocker(spec_name, camera)
            await pressure_mocker.start()
            pressure_config["host"] = "localhost"
            pressure_config["port"] = pressure_mocker.port
            servers.append(pressure_mocker)

    yield config

    for server in servers:
        server.stop()


@pytest.fixture
async def controllers(setup_servers):

    _controllers = []

    for spec_name, spec_config in setup_servers["specs"].items():
        _controllers.append(
            IEBController.from_config(
                spec_name,
                spec_config,
                wago_modules=setup_servers["wago_modules"],
            )
        )

    yield _controllers


@pytest.fixture()
async def actor(setup_servers):

    _actor = IEBActor.from_config(setup_servers)

    _actor = await clu.testing.setup_test_actor(_actor)  # type: ignore

    yield _actor

    _actor.mock_replies.clear()
    await _actor.stop()
