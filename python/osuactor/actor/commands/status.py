#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Taeeun Kim, Mingyeong Yang (mingyeong@khu.ac.kr)
# @Date: 2021-04-01
# @Filename: status.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)
#add by MY, 2021-04-01

from __future__ import annotations

from clu.command import Command

from osuactor.controller.controller import OsuController
from osuactor.exceptions import ArchonError

from ..tools import check_controller, error_controller, parallel_controllers
from . import parser


@parser.command()
@parallel_controllers()
async def status(command: Command, controller: OsuController):
    """Reports the status of the controller."""
    if not check_controller(command, controller):
        return

    try:
        status = await controller.get_status()
    except OsuError as ee:
        return error_controller(command, controller, str(ee))

    command.info(
        status={
            "controller": controller.name,
            "status": controller.status.name,
            **status,
        }
    )

    return True
