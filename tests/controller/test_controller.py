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

@pytest.mark.asyncio
async def test_shutter_status(shutter: IebController):
    
    assert shutter.host == "localhost"
    assert shutter.name == "shutter"
    
    tasks_open = []
    for i in range(1):
        tasks_open.append(shutter.send_command('status'))

    await asyncio.gather(*tasks_open)
    

# check the pending time of normal sequence of opening the hartmann_door and closing the door after opening
@pytest.mark.asyncio
async def test_hartmann_door_open_close_lock_test(hartmann_right: IebController):
    assert hartmann_right.host == "localhost"
    assert hartmann_right.name == "hartmann_right"
    assert hartmann_right.hartmann_right_status == None
    
    tasks = []
    
    for i in range(1):
        tasks.append(hartmann_right.send_command('open'))
        tasks.append(hartmann_right.send_command('close'))

    await asyncio.gather(*tasks)
    

@pytest.mark.asyncio
async def test_hartmann_door_right_open_close_again(hartmann_right: IebController):
    assert hartmann_right.host == "localhost"
    assert hartmann_right.name == "hartmann_right"
    
    #initial state is 'None'
    await hartmann_right.send_command('open')
    assert hartmann_right.hartmann_right_status == 'opened'
     
    await hartmann_right.send_command('close')
    assert hartmann_right.hartmann_right_status == 'closed'
    
    
@pytest.mark.asyncio
async def test_hartmann_door_left_open_close(hartmann_left: IebController):

    assert hartmann_left.host == "localhost"
    assert hartmann_left.name == "hartmann_left"
    
    assert hartmann_left.hartmann_left_status == None
    await hartmann_left.send_command('status')
    assert hartmann_left.hartmann_left_status == 'closed'
  
    await hartmann_left.send_command('open')
    assert hartmann_left.hartmann_left_status == 'opened'
    
    await hartmann_left.send_command('close')
    assert hartmann_left.hartmann_left_status == 'closed'
    
@pytest.mark.asyncio
async def test_shutter_exposure(shutter: IebController):

    assert shutter.host == "localhost"
    assert shutter.name == "shutter"
    
    for i in range(1):
        await shutter.send_command('open')      
        assert shutter.shutter_status == 'opened'
        
        #1 second exposure
        await asyncio.sleep(1)
        
        await shutter.send_command('close')
        assert shutter.shutter_status == 'closed'

@pytest.mark.asyncio
async def test_hartmann_and_shutters(hartmann_right: IebController, hartmann_left:IebController, shutter:IebController):
    assert shutter.host == "localhost"
    assert shutter.name == "shutter"
    
    assert hartmann_left.host == "localhost"
    assert hartmann_left.name == "hartmann_left"

    assert hartmann_right.host == "localhost"
    assert hartmann_right.name == "hartmann_right"

    tasks_open = []

    tasks_open.append(hartmann_right.send_command('open'))
    tasks_open.append(hartmann_left.send_command('open'))
    tasks_open.append(shutter.send_command('open'))

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
