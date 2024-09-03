import asyncio
import unittest


from aiter import preload_aiter, push_aiter

from .helpers import get_n


class test_aitertools(unittest.TestCase):
    def test_preload_aiter(self):
        async def go():
            q = push_aiter()
            await q.push(*list(range(1000)))
            q.stop()

            self.assertEqual(len(q), 1000)
            aiter = preload_aiter(50, q)

            self.assertEqual(len(q), 1000)

            r = await get_n(aiter, 1)
            self.assertEqual(len(q), 949)
            self.assertEqual(r, [0])

            r = await get_n(aiter, 10)
            self.assertEqual(r, list(range(1, 11)))
            # we don't really know how many are left but it should be in this range
            self.assertTrue(939 <= len(q) <= 949)
            await asyncio.sleep(0)
            self.assertEqual(len(q), 939)

            r = await get_n(aiter)
            self.assertEqual(r, list(range(11, 1000)))
            self.assertEqual(len(q), 0)

        asyncio.run(go())
