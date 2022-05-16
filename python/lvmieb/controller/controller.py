#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from lvmieb.controller.motor import MotorController
from lvmieb.controller.pressure import PressureTransducer
from lvmieb.controller.wago import IEBWAGO


class IEBController:
    """Talks to an Ieb controller over TCP/IP

    This class mainly combines the different subsystem controllers (WAGO,
    motors, transducers) under a common umbrella.

    """

    def __init__(
        self,
        spec: str,
        wago: IEBWAGO,
        pressure: list[PressureTransducer] = [],
        motors: list[MotorController] = [],
    ):

        self.spec = spec

        self.wago = wago
        self.pressure = {p.camera: p for p in pressure}
        self.motors = {m.type: m for m in motors}

    @classmethod
    def from_config(cls, spec: str, config: dict, wago_modules: dict = {}):
        """Creates an instance of `.IEBController` from a configuration file."""

        wago_config = config["wago"].copy()
        wago_config["modules"] = wago_modules.copy()

        wago = IEBWAGO.from_config(wago_config, name=spec)

        motors = []
        for motor, motor_config in config.get("motor_controllers", {}).copy().items():
            motors.append(MotorController(spec, motor, **motor_config, wago=wago))

        pressure = []
        for camera, pressure_config in config.get("pressure", {}).copy().items():
            pressure.append(PressureTransducer(spec, camera, **pressure_config))

        return cls(spec, wago, pressure=pressure, motors=motors)
