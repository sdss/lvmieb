#this code is for example _CK 2021/03/30

import asyncio

async def send_message(message):
    reader, writer = await asyncio.open_connection(
        '10.7.45.27', 7776)

    sclHead = chr(0)+chr(7)
    sclTail = chr(13)

    sclStr = sclHead + message.upper() + sclTail

    print(f'Send: {message!r}')
    writer.write(sclStr.encode())
    await writer.drain()

    status, Reply = await receive_status(reader)
    print('status : ', status)
    print('reply : ', Reply)
    print('Close the connection')
    writer.close()
    await writer.wait_closed()

async def receive_status(areader):
    KeepGoing = True
    while KeepGoing:
            sclReply = ""
            data = await areader.read(4096)
            recStr = data.decode()
            sclReply = recStr[2:-1]

            if sclReply[:4] == 'DONE':
                print(sclReply[:4])
                return True, sclReply
            if sclReply[:3] == 'ERR':
                print(sclReply[:3])
                return True, sclReply
            if sclReply[:2] == 'IS':
                print(sclReply[:2])
                return True, sclReply

asyncio.run(send_message('QX4'))
