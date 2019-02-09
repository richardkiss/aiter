import asyncio

from .push_aiter import push_aiter


async def active_aiter(aiter):
    """
    Wrap an aiter with an active puller that yanks out the items
    and puts them into a push_q.
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
