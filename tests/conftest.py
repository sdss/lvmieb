#!/usr/bin/env python
# -*- coding: utf-8 -*-


# @pytest.fixture()
# async def actor(mocker):

#     # We need to call the actor .start() method to force it to create the
#     # controllers and to start the tasks, but we don't want to run .start()
#     # on the actor.

#     mocker.patch.object(AMQPBaseActor, "start")

#     _actor = IEBA.from_config(test_config)

#     _actor.parser_args = [controllers]
#     await _actor.start()

#     _actor = await clu.testing.setup_test_actor(_actor)  # type: ignore

#     yield _actor

#     _actor.mock_replies.clear()
#     await _actor.stop()
