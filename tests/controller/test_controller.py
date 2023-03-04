#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-13
# @Filename: test_controller.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

from typing import TYPE_CHECKING

from ..mockers import WAGOMocker


if TYPE_CHECKING:
    from lvmieb.controller import IEBController


async def test_controller(controllers: list[IEBController]):
    assert len(controllers) == 2

    controller = controllers[0]

    assert controller.spec == "sp1"

    assert controller.wago is not None
    assert isinstance(controller.wago, WAGOMocker)

    assert controller.pressure is not None
    assert isinstance(controller.pressure, dict)
    assert len(controller.pressure) == 3

    assert controller.motors is not None
    assert isinstance(controller.motors, dict)
    assert len(controller.motors) == 3
