import asyncio

from .push_aiter import push_aiter


async def active_aiter(aiter):
    """
    Wrap an aiter with a task that actively yanks out the items
    and puts them into a push_q.

    This might be useful if you have an iterator that needs its elements
    pulled out as soon as they are created and cached in memory, even if
    the consumer is not yet ready. Be careful though, since getting too
    far behind can mean lots of memory is consumed, especially if each
    element uses a lot of memory.
    """
    q = push_aiter()

    async def _pull_task(aiter):
        async for _ in aiter:
            q.push(_)
        q.stop()

    task = asyncio.ensure_future(_pull_task(aiter))

    async for _ in q:
        yield _
    await task
