import asyncio

from aiter.remote import RPCStream

from examples.irc.apis import MyJSONMessage, MemberAPI, ServerAPI


async def sample(server_api):
    member = MemberAPI("foo")
    room = await server_api.room_for_name("foo")
    await room.join(member)
    await room.send_msg("hello all")


async def pipeline(sr, sw, rpc_stream):
    try:
        while True:
            line = await sr.readline()
            if len(line) == 0:
                break
            msg = MyJSONMessage.deserialize(line)
            await rpc_stream.handle_message(msg)
    except Exception as ex:
        print(ex)
    sw.close()


async def main():
    sr, sw = await asyncio.open_connection("127.0.0.1", 7777)

    async def push_to_sw(msg):
        blob = msg.serialize()
        sw.write(blob)
        sw.write(b"\n")

    rpc_stream = RPCStream(None, push_to_sw, MyJSONMessage)

    server_api = rpc_stream.remote_obj(ServerAPI, 0)

    task = asyncio.ensure_future(pipeline(sr, sw, rpc_stream))

    try:
        await sample(server_api)
    except Exception as ex:
        print(ex)

    await task


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
