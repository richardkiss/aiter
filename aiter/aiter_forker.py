import asyncio

from .push_aiter import push_aiter


def aiter_forker(aiter):
    """
    Wrap an iterator with push_aiter. This can also be forked.
    """

    open_aiter = aiter.__aiter__()

    async def worker(open_aiter, pa):
        try:
            _ = await open_aiter.__anext__()
            if not pa.is_stopped():
                pa.push(_)
        except StopAsyncIteration:
            pa.stop()

    def make_kick():
        def kick(pa):
            if pa.head().task and not pa.head().task.done():
                return
            pa.head().task = asyncio.ensure_future(worker(open_aiter, pa))
        return kick

    pa = push_aiter(next_preflight=make_kick())
    pa.head().task = asyncio.ensure_future(worker(open_aiter, pa))
    return pa
