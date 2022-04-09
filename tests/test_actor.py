import pytest

from lvmieb.actor.actor import lvmieb as IebActor


@pytest.mark.asyncio
async def test_actor(actor: IebActor):

    assert actor


@pytest.mark.asyncio
async def test_ping(actor: IebActor):

    command = await actor.invoke_mock_command("ping")
    await command

    assert command.status.did_succeed
    assert len(command.replies) == 2
    assert command.replies[1].message["text"] == "Pong."


@pytest.mark.asyncio
async def test_actor_no_config():

    with pytest.raises(RuntimeError):
        IebActor.from_config(None)
