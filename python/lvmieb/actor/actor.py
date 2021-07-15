#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Taeeun Kim, Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-03-22
# @Filename: actor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations, print_function, division, absolute_import

import asyncio
import os
import warnings
from contextlib import suppress

from lvmieb import __version__  #added by CK 2021/03/30
#from lvmieb.controller.command import lvmCommand #changed by CK 2021/03/30
from lvmieb.controller.controller import IebController #changed by CK 2021/03/30
from lvmieb.exceptions import LvmIebUserWarning
from clu.actor import AMQPActor

from .commands import parser as lvm_command_parser #added by CK 2021/03/30


__all__ = ["lvmieb"]                             #changed by CK 2021/03/30

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
        **kwargs,
    ):
        self.controllers = {c.name: c for c in controllers}
        self.parser_args = [self.controllers]
        super().__init__(*args, **kwargs)

#Changgon changed the under part 2021/03/30

    async def start(self):
        """Start the actor and connect the controllers."""

        connect_timeout = self.config["timeouts"]["controller_connect"]

        """
        #cannot use this part for now.. we will develop the code for the timeout error eventually
        for controller in self.controllers.values():
            try:
                await asyncio.wait_for(controller.send_command('init'), timeout=connect_timeout)
            except asyncio.TimeoutError:
                warnings.warn(
                    f"Timeout out connecting to {controller.name!r}.",
                    LvmIebUserWarning,
                )
        """
                
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
        
        if "controllers" in instance.config:
            controllers = (
                IebController(
                    host = ctr["host"],
                    port = ctr["port"],
                    name=ctrname,
                )
                for (ctrname, ctr) in instance.config["controllers"].items()
            )
            #for c in controllers:
            #    print(c.name, c.port, c.host)
            instance.controllers = {c.name: c for c in controllers}
            instance.parser_args = [instance.controllers]
            
        return instance

