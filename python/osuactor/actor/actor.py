#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Taeeun Kim, Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-03-22
# @Filename: actor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
import os
import warnings
from contextlib import suppress

from osuactor import __version__  #added by CK 2021/03/30
#from osuactor.controller.command import OsuCommand #changed by CK 2021/03/30
from osuactor.controller.controller import OsuController #changed by CK 2021/03/30
from clu.actor import AMQPActor

from .commands import parser as osu_command_parser #added by CK 2021/03/30


__all__ = ["OsuActor"]                             #changed by CK 2021/03/30

class OsuActor(AMQPActor):
    """OSU Spectrograph controller actor.
    In addition to the normal arguments and keyword parameters for
    `~clu.actor.AMQPActor`, the class accepts the following parameters.
    """ 
    parser = osu_command_parser

    def __init__(
        self,
        *args,
        controllers: tuple[OsuController, ...] = (),
        **kwargs,
    ):
        self.controllers = {c.name: c for c in controllers}
        self.parser_args = [self.controllers]
#        super().new_user()
        super().__init__(*args, **kwargs)

#Changgon changed the under part 2021/03/30

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

#        self._status_jobs = [
#            asyncio.create_task(self._report_status(controller))   #need to be added after the hardware status commands are defined _CK 2021/03/30
#            for controller in self.controllers.values()
#        ]

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

