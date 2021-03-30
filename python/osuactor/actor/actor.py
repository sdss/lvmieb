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

from osuactor import __version__
from osuactor.controller.command import OsuCommand
from osuactor.controller.controller import OsuController
from clu.actor import AMQPActor

from .commands import parser as osu_command_parser


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

######################## Mingyeong code #############################
     
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

        self.name = "OsuActor"
        super().__init__(*args, **kwargs)

        self.observatory = os.environ.get("OBSERVATORY", "LCO")
        self.version = "0.1.0"

        self.user = "guest"
        self.password = "guest"
        self.host = "localhost"
        self.port = 5672
    
    async def start(self):
        """Start the actor and connect the controllers."""

        connect_timeout = self.config["timeouts"]["controller_connect"]

        for controller in self.controllers.values():
            try:
                await asyncio.wait_for(controller.start(), timeout=connect_timeout)
            except asyncio.TimeoutError:
                warnings.warn(
                    f"Timeout out connecting to {controller.name!r}.",
                    OsuActorUserWarning,
                )

        await super().start()

       # self._status_jobs = [
        #    asyncio.create_task(self._report_status(controller))
         #   for controller in self.controllers.values()
        #]

    async def stop(self):
        with suppress(asyncio.CancelledError):
            for task in self._fetch_log_jobs:
                task.cancel()
                await task
        return super().stop()

    @classmethod
    def from_config(cls, config, *args, **kwargs):
        """Creates an actor from a configuration file."""
        instance = super(OsuActor, cls).from_config(config, *args, **kwargs)
        assert isinstance(instance, OsuActor)
        if "controllers" in instance.config:
            controllers = (
                OsuController(
                    ctr["host"],
                    ctr["port"],
                    name=ctrname,
                )
                for (ctrname, ctr) in instance.config["controllers"].items()
            )
            instance.controllers = {c.name: c for c in controllers}
            instance.parser_args = [instance.controllers]  # Need to refresh this
        return instance
