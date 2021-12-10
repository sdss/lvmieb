import pytest

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
