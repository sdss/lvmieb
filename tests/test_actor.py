import os

import pytest
from clu import JSONActor
from clu.testing import setup_test_actor

from sdsstools.logger import get_logger
from lvmieb.actor.commands import parser as lvmieb_command_parser

from lvmieb.controller.controller import IebController

@pytest.fixture
def controllers(shutter: IebController, hartmann_left: IebController, hartmann_right: IebController):
    
    controllers = {}
    controllers.update({shutter.name: shutter})
    controllers.update({hartmann_right.name: hartmann_right})
    controllers.update({hartmann_left.name: hartmann_left})

    return controllers


async def send_command(actor, command_string):
    command = actor.invoke_mock_command(command_string)
    await command
    assert command.status.is_done

    # print("number of swithces are ",len(actor.parser_args[0]))
    switch_num = len(actor.parser_args[0])
    status_reply = actor.mock_replies[-1]
    #print(status_reply)
    #print(f"status reply is {status_reply}")
    return status_reply


@pytest.mark.asyncio
async def test_actor(controllers):

    test_actor = await setup_test_actor(JSONActor("lvmieb", host="localhost", port=9999))

    test_actor.parser = lvmieb_command_parser
    test_actor.parser_args = [controllers]
    
    status = await send_command(test_actor, "shutter open sp1")
    assert status["sp1"]["shutter"] == "opened"

    status = await send_command(test_actor, "shutter close sp1")
    assert status["sp1"]["shutter"] == "closed"

