#added by CK 2021/03/30
from __future__ import annotations

from clu.command import Command

from osuactor.controller.controller import OsuController
from osuactor.exceptions import OsuActorError

#from ..tools import check_controller, error_controller, parallel_controllers
from . import parser


@parser.command()
async def open(command: Command, controller: OsuController):




    return True
