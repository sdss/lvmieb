import pytest

from lvmieb.actor.actor import lvmieb as IebActor


@pytest.mark.asyncio
async def test_transducer_status(actor: IebActor):

    # initial state with the linear gauges are not initialized
    print(actor.parser_args[0])
    assert actor.parser_args[0]["r1"].pres_id == 253
    assert actor.parser_args[0]["r1"].trans_pressure == -1.0
    assert actor.parser_args[0]["r1"].trans_temp == -1.0

    assert actor.parser_args[0]["b1"].pres_id == 253
    assert actor.parser_args[0]["b1"].trans_pressure == -1.0
    assert actor.parser_args[0]["b1"].trans_temp == -1.0

    assert actor.parser_args[0]["z1"].pres_id == 253
    assert actor.parser_args[0]["z1"].trans_pressure == -1.0
    assert actor.parser_args[0]["z1"].trans_temp == -1.0

    command = await actor.invoke_mock_command("transducer status")
    await command
    assert command.status.did_succeed

    assert actor.parser_args[0]["r1"].trans_pressure == 0.0001738
    assert actor.parser_args[0]["r1"].trans_temp == 23.15
    assert actor.parser_args[0]["b1"].trans_pressure == 0.0002418
    assert actor.parser_args[0]["b1"].trans_temp == 23.09
    assert actor.parser_args[0]["z1"].trans_pressure == 0.0001742
    assert actor.parser_args[0]["z1"].trans_temp == 22.03

    assert command.replies[-2].message["sp1"]["r1_pressure"] == 0.0001738
    assert command.replies[-2].message["sp1"]["r1_temperature"] == 23.15
    assert command.replies[-2].message["sp1"]["b1_pressure"] == 0.0002418
    assert command.replies[-2].message["sp1"]["b1_temperature"] == 23.09
    assert command.replies[-2].message["sp1"]["z1_pressure"] == 0.0001742
    assert command.replies[-2].message["sp1"]["z1_temperature"] == 22.03
