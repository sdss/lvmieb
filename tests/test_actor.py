import pytest
from clu import JSONActor
from clu.testing import setup_test_actor

from lvmieb.actor.commands import parser as lvmieb_command_parser
from lvmieb.controller.controller import IebController


@pytest.fixture
def controllers(
    shutter: IebController, hartmann_left: IebController, hartmann_right: IebController
):

    controllers = {}
    controllers.update({shutter.name: shutter})
    controllers.update({hartmann_right.name: hartmann_right})
    controllers.update({hartmann_left.name: hartmann_left})

    return controllers


async def send_command(actor, command_string):
    command = actor.invoke_mock_command(command_string)
    await command
    assert command.status.is_done

    status_reply = actor.mock_replies[-1]
    return status_reply


# 20210916 changgon working on unit testing for shutter.
# need to add more unit tests. Don't use JsonActor -> Jose's comment..


@pytest.mark.asyncio
async def test_actor(controllers):

    test_actor = await setup_test_actor(
        JSONActor("lvmieb", host="localhost", port=9999)
    )

    test_actor.parser = lvmieb_command_parser
    test_actor.parser_args = [controllers]

    status = await send_command(test_actor, "shutter open sp1")
    assert status["sp1"]["shutter"] == "opened"

    status = await send_command(test_actor, "shutter close sp1")
    assert status["sp1"]["shutter"] == "closed"
