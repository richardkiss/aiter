import asyncio
import logging


async def map_aiter(map_f, aiter):
    """
    Take an async iterator and a map function, and apply the function
    to everything coming out of the iterator before passing it on.
    """
    if asyncio.iscoroutinefunction(map_f):
        _map_f = map_f
    else:
        async def _map_f(_):
            return map_f(_)

    async for _ in aiter:
        try:
            yield await _map_f(_)
        except Exception:
            logging.exception("unhandled mapping function %s worker exception on %s", map_f, _)
