import asyncio

from .push_aiter import push_aiter


def aiter_forker(aiter):
    """
    If you have an aiter that you would like to fork (split into multiple
    iterators, each of which produces the same elements), wrap it with this
    function.

    Returns a :class:`aiter.push_aiter <push_aiter>` object that will yield
    the same objects in the same order. This object supports
    :py:func:`fork <aiter.push_aiter.fork>`, which will let you create a
    duplicate stream.
    """

    open_aiter = aiter.__aiter__()

    async def worker(open_aiter, pa):
        try:
            _ = await open_aiter.__anext__()
            if not pa.is_stopped():
                pa.push(_)
        except StopAsyncIteration:
            pa.stop()
        pa.head().event.clear()

    def make_kick():
        def kick(pa):
            event = pa.head().event
            if event.is_set():
                return
            event.set()
            pa.head().task = asyncio.ensure_future(worker(open_aiter, pa))
        return kick

    pa = push_aiter(next_preflight=make_kick())
    pa.head().event = asyncio.Event()
    pa.head().event.set()
    pa.head().task = asyncio.ensure_future(worker(open_aiter, pa))
    return pa
