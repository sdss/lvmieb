#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-03-22
# @Filename: actor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
import os
import warnings
from contextlib import suppress

from osuactor.controller.command import OsuCommand
from osuactor.controller.controller import OsuController
from clu.actor import AMQPActor

__all__ = ["OsuActor"]

class OsuActor(AMQPActor):
    """OSU Spectrograph controller actor.
    In addition to the normal arguments and keyword parameters for
    `~clu.actor.AMQPActor`, the class accepts the following parameters.
    Parameters
    ----------
    controllers
        The list of `OsuController` instances to manage. (TBD)
    """

    #parser = Osu_command_parser

    def __init__(
        self,
        *args,
        controllers: tuple[OsuController, ...] = (),
        **kwargs,
    ):
        #: dict[str, OsuController]: A mapping of controller name to controller.
        self.controllers = {c.name: c for c in controllers}

        self.parser_args = [self.controllers]

        super().__init__(*args, **kwargs)

        self.observatory = os.environ.get("OBSERVATORY", "LCO")
        self.version = "0.1.0"

        self.name = "osu_actor"
        self.user = "guest"
        self.password = "guest"
        self.host = "localhost"
        self.port = 5672
