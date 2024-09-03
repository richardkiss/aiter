import asyncio
import unittest


from aiter import iter_to_aiter, gated_aiter

from .helpers import get_n


class test_aitertools(unittest.TestCase):
    def test_gated_aiter(self):
        async def go():
            ai = iter_to_aiter(range(3000000000))
            aiter = gated_aiter(ai)
            await aiter.push(9)
            r = await get_n(aiter, 3)
            r.extend(await get_n(aiter, 4))
            await aiter.push(11)
            aiter.stop()
            r.extend(await get_n(aiter))
            self.assertEqual(r, list(range(20)))

        asyncio.run(go())
