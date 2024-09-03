import asyncio
import unittest

from aiter import aiter_forker, push_aiter

from .helpers import run, get_n


class test_aiter_forker(unittest.TestCase):
    def test_aiter_forker(self):
        async def go():
            q = push_aiter()
            forker = aiter_forker(q)
            await q.push(1, 2, 3, 4, 5)
            r0 = await get_n(forker, 3)
            f2 = forker.fork()
            await q.push(*range(7, 14))
            q.stop()
            r1 = await get_n(forker)
            r2 = await get_n(f2)

            self.assertEqual(r0, [1, 2, 3])
            self.assertEqual(r1, [4, 5, 7, 8, 9, 10, 11, 12, 13])
            self.assertEqual(r2, [4, 5, 7, 8, 9, 10, 11, 12, 13])

        asyncio.run(go())

    def test_aiter_forker_multiple_active(self):
        """
        Multiple forks of an aiter_forker both asking for empty q information
        at the same time. Make sure the second one doesn't block.
        """

        async def go():
            q = push_aiter()
            forker = aiter_forker(q)
            fork_1 = forker.fork(is_active=True)
            fork_2 = forker.fork(is_active=True)
            f1 = asyncio.ensure_future(get_n(fork_1, 1))
            f2 = asyncio.ensure_future(get_n(fork_2, 1))
            await asyncio.wait([f1, f2], timeout=0.1)
            self.assertFalse(f1.done())
            self.assertFalse(f2.done())
            await q.push(1)
            await asyncio.wait([f1, f2], timeout=0.1)
            self.assertTrue(f1.done())
            self.assertTrue(f2.done())
            r1 = await f1
            r2 = await f2
            self.assertEqual(r1, [1])
            self.assertEqual(r2, [1])

        asyncio.run(go())
