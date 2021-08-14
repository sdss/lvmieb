#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Taeeun Kim, Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-03-22
# @Filename: actor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

"""
isort:skip_file
"""

from __future__ import absolute_import, annotations, division, print_function

import asyncio
from contextlib import suppress

from clu.actor import AMQPActor

from lvmieb import __version__  # added by CK 2021/03/30
from lvmieb.controller.controller import IebController  # isort:skip

from .commands import parser as lvm_command_parser  # added by CK 2021/03/30

__all__ = ["lvmieb"]  # changed by CK 2021/03/30


class lvmieb(AMQPActor):
    """lvm Spectrograph controller actor.
    In addition to the normal arguments and keyword parameters for
    `~clu.actor.AMQPActor`, the class accepts the following parameters.

    parameters
    ----------
    controllers
        The list of '.IebController' instances to manage.
    """

    parser = lvm_command_parser

    def __init__(
        self,
        *args,
        controllers: tuple[IebController, ...] = (),
        wago_controllers: tuple[IebController, ...] = (),
        **kwargs,
    ):
        self.controllers = {c.name: c for c in controllers}
        self.parser_args = [self.controllers]
        self.version = __version__
        super().__init__(*args, **kwargs)

    # Changgon changed the under part 2021/03/30

    async def start(self):
        """Start the actor and connect the controllers."""
        await super().start()

    async def stop(self):
        with suppress(asyncio.CancelledError):
            for task in self._fetch_log_jobs:
                task.cancel()
                await task
        return super().stop()

    @classmethod
    def from_config(cls, config, *args, **kwargs):
        """Creates an actor from a configuration file."""
        instance = super(lvmieb, cls).from_config(config, *args, **kwargs)
        assert isinstance(instance, lvmieb)
        assert isinstance(instance.config, dict)
        # print(instance.config["devices"]["motor_controllers"]["sp1"])

        if "sp1" in instance.config["devices"]["motor_controllers"]:
            controllers = (
                IebController(
                    host=ctr["host"], port=ctr["port"], name=ctrname, spec="sp1"
                )
                for (ctrname, ctr) in instance.config["devices"]["motor_controllers"][
                    "sp1"
                ].items()
            )
            instance.controllers = {c.name: c for c in controllers}
            # print(instance.controllers)
            # instance.parser_args = [instance.controllers]

        if "sp1" in instance.config["devices"]["wago"]["controllers"]:
            controllers = (
                IebController(
                    host=ctr["address"], port=ctr["port"], name=ctrname, spec="sp1"
                )
                for (ctrname, ctr) in instance.config["devices"]["wago"][
                    "controllers"
                ].items()
            )
            instance.controllers.update({c.name: c for c in controllers})
            # print(instance.controllers)
            # instance.parser_args = [instance.controllers]

        if "sp1" in instance.config["devices"]["pressure"]:
            controllers = (
                IebController(
                    host=ctr["host"],
                    port=ctr["port"],
                    pres_id=ctr["id"],
                    name=ctrname,
                    spec="sp1",
                )
                for (ctrname, ctr) in instance.config["devices"]["pressure"][
                    "sp1"
                ].items()
            )
            instance.controllers.update({c.name: c for c in controllers})
            print(instance.controllers)
            instance.parser_args = [instance.controllers]

        return instance
