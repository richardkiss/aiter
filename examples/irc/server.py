import asyncio

from aiter import join_aiters, map_aiter
from aiter.remote import RPCStream
from aiter.server import start_server_aiter

from examples.irc.apis import MyJSONMessage, ServerAPI


def create_pipeline(server, aiter, server_api):
    async def pair_to_connection(pair):
        sr, sw = pair

        async def push_to_sw(msg):
            blob = msg.serialize()
            sw.write(blob)
            sw.write(b"\n")

        rpc_stream = RPCStream(None, push_to_sw, MyJSONMessage)
        source = rpc_stream.register_local_obj(server_api)
        assert source == 0
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
        yield "done"

    aiter_1 = map_aiter(pair_to_connection, aiter)
    return join_aiters(aiter_1)


async def run_server():
    server_api = ServerAPI()

    server, aiter = await start_server_aiter(7777)

    pipeline_aiter = create_pipeline(server, aiter, server_api)

    async for _ in pipeline_aiter:
        print(_)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run_server())
