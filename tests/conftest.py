#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import pathlib
from contextlib import suppress

import pytest

import clu.testing
from sdsstools import read_yaml_file

from lvmieb.actor import IEBActor
from lvmieb.controller import IEBController

from .mockers import DepthMocker, MotorMocker, PressureMocker, WAGOMocker


@pytest.fixture
def config():

    config_file = pathlib.Path(__file__).parent / "./test_lvmieb.yml"
    yield read_yaml_file(str(config_file))


@pytest.fixture
async def setup_servers(config, mocker):

    mocker.patch("lvmieb.controller.controller.IEBWAGO", WAGOMocker)

    servers = {}
    for spec_name, spec_config in config["specs"].items():
        for motor_type, motor_config in spec_config["motor_controllers"].items():
            motor_mocker = MotorMocker(spec_name, motor_type=motor_type)
            await motor_mocker.start()
            motor_config["host"] = "localhost"
            motor_config["port"] = motor_mocker.port
            servers[f"{spec_name}_{motor_type}"] = motor_mocker
        for camera, pressure_config in spec_config["pressure"].items():
            pressure_mocker = PressureMocker(spec_name, camera)
            await pressure_mocker.start()
            pressure_config["host"] = "localhost"
            pressure_config["port"] = pressure_mocker.port
            servers[f"{spec_name}_pressure_{camera}"] = pressure_mocker

    servers["depth"] = DepthMocker()
    await servers["depth"].start()
    config["depth_gauges"]["host"] = "localhost"
    config["depth_gauges"]["port"] = servers["depth"].port

    yield servers

    with suppress():
        for server in servers.values():
            server.stop()


@pytest.fixture
async def controllers(setup_servers, config):

    _controllers = []

    for spec_name, spec_config in config["specs"].items():
        _controllers.append(
            IEBController.from_config(
                spec_name,
                spec_config,
                wago_modules=config["wago_modules"],
            )
        )

    yield _controllers


@pytest.fixture()
async def actor(config, setup_servers):

    _actor = IEBActor.from_config(config)
    _actor.parser_args = [_actor.controllers]

    _actor = await clu.testing.setup_test_actor(_actor)  # type: ignore

    yield _actor

    _actor.mock_replies.clear()
    await _actor.stop()
