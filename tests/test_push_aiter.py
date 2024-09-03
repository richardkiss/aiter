import asyncio
import unittest

import pytest

from aiter import push_aiter


from .helpers import get_n


class test_aitertools(unittest.TestCase):
    def test_push_aiter(self):
        async def go():
            q = push_aiter()
            self.assertEqual(len(q), 0)
            await q.push(5, 4)
            self.assertEqual(len(q), 2)
            await q.push(3)
            self.assertEqual(len(q), 3)
            q.stop()
            with pytest.raises(ValueError):
                await q.push(2)
            results = list(q.available_iter())
            self.assertEqual(results, [5, 4, 3])
            results = await get_n(q)
            self.assertEqual(results, [5, 4, 3])

        asyncio.run(go())
