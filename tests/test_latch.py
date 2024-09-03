import asyncio
import unittest

import pytest

from aiter.latch import Latch


async def run_all_tasks(tasks):
    pending = tasks
    while len(pending) > 0:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for t in done:
            t.result()


class test_aitertools(unittest.TestCase):
    def test_latch(self):
        async def go():
            reader_state = 0
            writer_state = 0

            async def go_writer(latch):
                nonlocal reader_state, writer_state
                writer_state = 1
                assert reader_state in [0, 1]
                await latch.push(101)
                writer_state = 2

                assert reader_state in [0, 1]
                await latch.push(102)
                writer_state = 3

                assert reader_state in [1, 2]

                await latch.push(103)
                writer_state = 4
                assert reader_state in [2, 3]

                await latch.push(104)
                writer_state = 5
                latch.close()
                assert reader_state in [4, 5]

                with pytest.raises(ValueError):
                    await latch.push(105)

            async def go_reader(latch):
                nonlocal reader_state, writer_state
                reader_state = 1
                assert writer_state in [0, 1, 2]
                t = await latch.pull()

                assert t == 101
                assert writer_state in [1, 2]
                reader_state = 2
                t = await latch.pull()

                assert t == 102
                assert writer_state in [2, 3]
                reader_state = 3

                t = await latch.pull()

                assert t == 103
                assert writer_state in [3, 4]
                reader_state = 4

                t = await latch.pull()

                assert t == 104
                assert writer_state in [4, 5]
                reader_state = 5

                with pytest.raises(StopAsyncIteration):
                    await latch.pull()

            latch = Latch()
            t0 = asyncio.create_task(go_writer(latch))
            t1 = asyncio.create_task(go_reader(latch))
            await run_all_tasks([t0, t1])
            with pytest.raises(ValueError):
                latch.close()
            return 100

        r = asyncio.run(go())
        assert r == 100
