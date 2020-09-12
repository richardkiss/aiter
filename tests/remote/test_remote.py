import asyncio
import unittest

from typing import Dict, List

from aiter import push_aiter
from aiter.remote import JSONMessage, RPCStream


class DemoAPI:
    def __init__(self, val):
        self.val = val

    async def inc(self, diff: int = 1) -> None:
        self.val += diff

    async def dec(self, diff: int = 1) -> None:
        self.val -= diff

    async def multiply(self, t: int) -> int:
        return self.val * t

    async def current_val(self) -> int:
        return self.val

    async def vowel_total(self, d: Dict[str, List[int]]) -> int:
        t = 0
        for k, v in d.items():
            if len(k) > 0 and k[0] in "aeiou":
                t += sum(v)
        return t


def async_push_for_push_aiter(pa: push_aiter):
    async def push(v):
        pa.push(v)

    return push


class test_remote(unittest.TestCase):
    def test_simple(self):
        pa1 = push_aiter()
        pa2 = push_aiter()

        api_1 = DemoAPI(200)
        rpc_1_to_2 = RPCStream(pa1, async_push_for_push_aiter(pa2), JSONMessage)
        rpc_1_to_2.register_local_obj(api_1, 0)

        api_2 = DemoAPI(300)
        rpc_2_to_1 = RPCStream(pa2, async_push_for_push_aiter(pa1), JSONMessage)
        rpc_2_to_1.register_local_obj(api_2, 0)

        remote_api_1 = rpc_2_to_1.remote_obj(DemoAPI, 0)
        remote_api_2 = rpc_1_to_2.remote_obj(DemoAPI, 0)

        async def do_async_tests():
            rpc_1_to_2.start()
            rpc_2_to_1.start()

            d = {"foo": [50, 60], "ark": [1000, 2002], "zoo": []}

            assert await api_1.current_val() == 200
            assert await api_2.current_val() == 300
            assert await remote_api_1.current_val() == 200
            assert await remote_api_2.current_val() == 300

            await remote_api_1.inc()
            assert await api_1.current_val() == 201
            assert await remote_api_1.current_val() == 201

            await remote_api_1.inc(20)
            assert await api_1.current_val() == 221
            assert await remote_api_1.current_val() == 221

            await remote_api_1.inc(diff=30)
            assert await api_1.current_val() == 251
            assert await remote_api_1.current_val() == 251

            assert await api_2.vowel_total(d) == 3002
            assert await remote_api_2.vowel_total(d) == 3002
            assert await api_2.vowel_total(d=d) == 3002
            assert await remote_api_2.vowel_total(d=d) == 3002

            try:
                await api_2.vowel_total(j=d)
                self.assertFalse("exception expected")
            except TypeError:
                pass

            try:
                r = await remote_api_1.vowel_total(j=d)
                self.assertFalse("exception expected")
            except OSError as ex:
                self.assertEqual(
                    ex.args[0], "vowel_total() got an unexpected keyword argument 'j'"
                )

        asyncio.run(do_async_tests())
