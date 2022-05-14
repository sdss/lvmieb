#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Taeeun Kim, Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-03-22
# @Filename: actor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import os
import pathlib
from copy import deepcopy
from typing import ClassVar

from yaml import warnings

from clu import Command
from clu.actor import AMQPActor
from sdsstools.configuration import read_yaml_file

from lvmieb import __version__, config
from lvmieb.controller.controller import IEBController
from lvmieb.controller.depth import DepthGauges
from lvmieb.exceptions import LvmIebUserWarning

from .commands import parser as lvm_command_parser


__all__ = ["IEBActor", "IEBCommand", "ControllersType"]


class IEBActor(AMQPActor):
    """LVM Spectrograph controller actor.

    In addition to the normal arguments and keyword parameters for
    `~clu.actor.AMQPActor`, the class accepts the following parameters.

    Parameters
    ----------
    controllers
        The list of '.IEBController' instances to manage.

    """

    parser = lvm_command_parser
    BASE_CONFIG: ClassVar[str | dict | None] = config

    def __init__(
        self,
        *args,
        controllers: tuple[IEBController, ...] = (),
        depth_gauges: DepthGauges | None = None,
        **kwargs,
    ):

        self.controllers = {c.spec: c for c in controllers}
        self.depth_gauges = depth_gauges

        self.version = __version__

        super().__init__(*args, **kwargs)

    async def start(self, **kwargs):  # pragma: no cover
        """Starts the actor connection to RabbitMQ."""

        # We wait to set this until here to make sure all the controllers
        # have been created.
        self.parser_args = [self.controllers]

        return await super().start(**kwargs)

    @classmethod
    def from_config(cls, config: dict | str | None, *args, **kwargs):
        """Creates an actor from a configuration file."""

        if config is None:
            if cls.BASE_CONFIG is None:
                raise RuntimeError("The class does not have a base configuration.")
            config = cls.BASE_CONFIG

        if isinstance(config, (str, pathlib.Path)):
            config = dict(read_yaml_file(str(config)))

        if "schema" in config["actor"]:
            schema = config["actor"]["schema"]
            if not os.path.isabs(schema):
                schema = os.path.join(
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "../")),
                    schema,
                )
            config["actor"]["schema"] = schema

        instance = super().from_config(config["actor"])

        controllers: list[IEBController] = []

        for spec in config.get("enabled_specs", []):
            if "specs" not in config or spec not in config["specs"]:
                warnings.warn(
                    f"Cannot find configuration for {spec!r}.",
                    LvmIebUserWarning,
                )
                continue

            spec_config = config["specs"][spec].copy()
            wago_modules = deepcopy(config.get("wago_modules", {}))

            controller = IEBController.from_config(
                spec,
                spec_config,
                wago_modules=wago_modules,
            )
            controllers.append(controller)

        instance.controllers = {contr.spec: contr for contr in controllers}

        if (depth_gauges := config.get("depth_gauges", None)) is not None:
            instance.depth_gauges = DepthGauges(**depth_gauges.copy())

        return instance


IEBCommand = Command[IEBActor]
ControllersType = dict[str, IEBController]
