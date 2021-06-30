#!/usr/bin/env python                                                                                                                                          
# -*- coding: utf-8 -*-
#
# @Author: Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-05-25
# @Filename: test_controller.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import pytest

from lvmieb.controller.controller import IebController
from lvmieb.exceptions import (
    LvmIebError,
    LvmIebNotImplemented,
    LvmIebAPIError,
    LvmIebApiAuthError,
    LvmIebMissingDependency,
    LvmIebWarning,
    LvmIebUserWarning,
    LvmIebSkippedTestWarning,
    LvmIebDeprecationWarning,
)

"""
# check the normal sequence of opening the hartmann_door and closing the door after opening
@pytest.mark.asyncio
async def test_hartmann_door_right_exposure(hartmann_right: IebController):
    assert hartmann_right.host == "localhost"
    assert hartmann_right.name == "hartmann_right"
    await hartmann_right.connect()
    assert hartmann_right.connected == True    
    assert hartmann_right.hartmann_right_status == 'closed'
    
    for i in range(1):
        await hartmann_right.send_command('open')
        assert hartmann_right.connected == True
        assert hartmann_right.hartmann_right_status == 'opened'
        
        #1 second exposure
        await asyncio.sleep(1)
        
        await hartmann_right.send_command('close')
        assert hartmann_right.hartmann_right_status == 'closed'
    
    await hartmann_right.disconnect()
    assert hartmann_right.connected == False


@pytest.mark.asyncio
async def test_hartmann_door_right_open_close_again(hartmann_right: IebController):
    assert hartmann_right.host == "localhost"
    assert hartmann_right.name == "hartmann_right"
    await hartmann_right.connect()
    
    #initial state is 'closed'
    assert hartmann_right.hartmann_right_status == 'closed'
    #await hartmann_right.send_command('close')

@pytest.mark.asyncio
async def test_hartmann_door_left_exposure(hartmann_left: IebController):

    assert hartmann_left.host == "localhost"
    assert hartmann_left.name == "hartmann_left"
    await hartmann_left.connect()
    
    assert hartmann_left.hartmann_left_status == 'closed'

    for i in range(1):
        await hartmann_left.send_command('open')
        assert hartmann_left.connected == True    
        assert hartmann_left.hartmann_left_status == 'opened'
        
        #1 second exposure
        await asyncio.sleep(1)
        
        await hartmann_left.send_command('close')
        assert hartmann_left.hartmann_left_status == 'closed'
    
    await hartmann_left.disconnect()
    assert hartmann_left.connected == False
    
@pytest.mark.asyncio
async def test_hartmann_door_left_open_close_again(hartmann_left: IebController):
    assert hartmann_left.host == "localhost"
    assert hartmann_left.name == "hartmann_left"
    await hartmann_left.connect()
    
    #initial state is 'closed'
    assert hartmann_left.hartmann_left_status == 'closed'
    #await hartmann_left.send_command('close')

@pytest.mark.asyncio
async def test_shutter_exposure(shutter: IebController):

    assert shutter.host == "localhost"
    assert shutter.name == "shutter"
    await shutter.connect()
    
    assert shutter.shutter_status == 'closed'

    for i in range(1):
        await shutter.send_command('open')
        assert shutter.connected == True       
        assert shutter.shutter_status == 'opened'
        
        #1 second exposure
        await asyncio.sleep(1)
        
        await shutter.send_command('close')
        assert shutter.shutter_status == 'closed'
    
    await shutter.disconnect()
    assert shutter.connected == False
    
@pytest.mark.asyncio
async def test_shutter_open_close_again(shutter: IebController):
    assert shutter.host == "localhost"
    assert shutter.name == "shutter"
    await shutter.connect()
    
    #initial state is 'closed'
    assert shutter.shutter_status == 'closed'
    #await shutter.send_command('close')

@pytest.mark.asyncio
async def test_hartmann_and_shutters(hartmann_right: IebController, hartmann_left:IebController, shutter:IebController):
    assert shutter.host == "localhost"
    assert shutter.name == "shutter"
    await shutter.connect()
    
    assert hartmann_left.host == "localhost"
    assert hartmann_left.name == "hartmann_left"
    await hartmann_left.connect()

    assert hartmann_right.host == "localhost"
    assert hartmann_right.name == "hartmann_right"
    await hartmann_right.connect()

    tasks_open = []

    tasks_open.append(hartmann_right.send_command('open'))
    assert hartmann_right.connected == True

    tasks_open.append(hartmann_left.send_command('open'))
    assert hartmann_left.connected == True

    tasks_open.append(shutter.send_command('open'))
    assert shutter.connected == True

    await asyncio.gather(*tasks_open)

    assert hartmann_right.hartmann_right_status == 'opened'
    assert hartmann_left.hartmann_left_status == 'opened'
    assert shutter.shutter_status == 'opened'

    tasks_close = []

    tasks_close.append(hartmann_right.send_command('close'))
    tasks_close.append(hartmann_left.send_command('close'))
    tasks_close.append(shutter.send_command('close'))

    await asyncio.gather(*tasks_close)

    assert hartmann_right.hartmann_right_status == 'closed'
    assert hartmann_left.hartmann_left_status == 'closed'
    assert shutter.shutter_status == 'closed'
    
"""

@pytest.mark.asyncio
async def test_connection(hartmann_right: IebController):
    assert hartmann_right.host == "localhost"
    assert hartmann_right.name == "hartmann_right"
    
    assert hartmann_right.hartmann_right_status == None
    await hartmann_right.send_command('open')
    
    #assert hartmann_right.connected == True
    assert hartmann_right.hartmann_right_status == 'opened'
    #await hartmann_right.send_command('close')
    #assert hartmann_right.hartmann_right_status == 'closed'
    
 