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
from osuactor.controller.command import OsuCommand #changed by CK 2021/03/30
from osuactor.controller.controller import OsuController #changed by CK 2021/03/30
from clu.actor import AMQPActor

from .commands import parser as osu_command_parser #added by CK 2021/03/30


__all__ = ["OsuActor"]                             #changed by CK 2021/03/30

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
     
    parser = osu_command_parser

    def __init__(
        self,
        *args,
        controllers: tuple[OsuController, ...] = (),
        **kwargs,
    ):
        #: dict[str, OsuController]: A mapping of controller name to controller.
        self.controllers = {c.name: c for c in controllers}

        self.parser_args = [self.controllers]

        if "schema" not in kwargs:
            kwargs["schema"] = os.path.join(
                    os.path.dirname(__file__),
                    "../etc/archon.json",
                    )

       #self.name = "OsuActor"
        super().__init__(*args, **kwargs)

        self.observatory = os.environ.get("OBSERVATORY", "LCO")
        self.version = __version__

        self._exposing: bool = False

        #self.user = "guest"
        #self.password = "guest"
        #self.host = "localhost"
        #self.port = 5672
   
########################################################################
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

        self._fetch_log_jobs = [                                                  ##add by MY 2021.04.01
                asyncio.create_task(self._fetch_log(controller))
                for controller in self.controllers.value()
                ]

       # self._status_jobs = [
        #    asyncio.create_task(self._report_status(controller))   #need to be added after the hardware status commands are defined _CK 2021/03/30
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

####################add by MY 2021.04.01###############################################3

    def can_expose(self) -> bool:
        """check if the actor can take a new exposure"""
        return self._exposing

"""
    async def _fetch_log(self, controller: OsuController):
        """Fetch the lof and outputs new messages"""
        while True:
            cmd: OsuCommand = await cotroller.send_command("FETCHLOG")
            if cmd.succeeded() and len(cmd.replies) == 1:
                if str(cmd.replies[0].reply) != "(null)":
                    self.write(
                            log=dict(
                                controller=controller.name,
                                log=str(cmd.replies[0].reply),
                                )
                            )
                            continue
                        await asyncio.sleep(1)

    async def _report_status(self, controller: OsuController):
        """Reports the status of the controller."""
        async for status in controller.yeild_status():
            self.write(
                    status=dict(
                        controller=controller.name,
                        status=status.name,
                        )
                    )
"""
