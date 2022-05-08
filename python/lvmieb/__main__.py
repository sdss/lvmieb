# -*- coding: utf-8 -*-
#
# @Author: Changging Kim, Mingyeong Yang, Taeeun Kim
# @Date: 2020-10-26
# @Filename: __main__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import os

import click
from click_default_group import DefaultGroup

from clu.tools import cli_coro as cli_coro_lvm
from sdsstools.daemonizer import DaemonGroup

from lvmieb.actor.actor import IEBActor


@click.group(cls=DefaultGroup, default="actor", default_if_no_args=True)
@click.option(
    "-c",
    "--config",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the user configuration file.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Debug mode. Use additional v for more details.",
)
@click.pass_context
def lvmieb(ctx, config_file, verbose):
    """LVM Electronics Box Controller."""

    ctx.obj = {"verbose": verbose, "config_file": config_file}


@lvmieb.group(cls=DaemonGroup, prog="lvmieb_actor", workdir=os.getcwd())
@click.pass_context
@cli_coro_lvm
async def actor(ctx):
    """Runs the actor."""

    default_config_file = os.path.join(os.path.dirname(__file__), "etc/lvmieb.yml")
    config_file = ctx.obj["config_file"] or default_config_file

    lvmieb_obj = IEBActor.from_config(config_file)

    if ctx.obj["verbose"]:
        lvmieb_obj.log.fh.setLevel(0)
        lvmieb_obj.log.sh.setLevel(0)

    await lvmieb_obj.start()
    await lvmieb_obj.run_forever()


if __name__ == "__main__":
    lvmieb()
