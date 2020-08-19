import asyncio


class DemoAPI:
    def __init__(self, v):
        self._v = v

    async def add(self, t: int) -> int:
        return self._v + t

    async def multiply(self, t: int) -> int:
        return self._v * t

    async def inc(self) -> None:
        self._v += 1


'''
You can run this demo from the command-line, using ipython
    
pip install ipython

SERVER:

ipython

import asyncio; from aiter.remote.demo import DemoAPI; from aiter.remote.websocket_server import simple_server; d = DemoAPI(100); await asyncio.Task(simple_server(12345, d))


CLIENT:

ipython
from aiter.remote.demo import DemoAPI; from aiter.remote.websocket_client import connect_to_remote_api; demo = await connect_to_remote_api("ws://127.0.0.1:12345/ws/", DemoAPI)
print(await demo.add(100))
print(await demo.inc())



TO LOG THE JSON, apply this patch:

--- a/aiter/remote/json_packaging.py
+++ b/aiter/remote/json_packaging.py
@@ -94,6 +94,7 @@ def text_to_target_source_msg(text):
     """
     This method converts a text string into a triple of (json_message, source, target)
     """
+    print(repr(text))
     d = json.loads(text)
     source = d.get("s")
     target = d.get("t", 0)

'''