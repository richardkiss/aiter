import asyncio
import logging


async def map_filter_aiter(map_f, aiter):
    """
    In this case, the map_f must return a list, which will be flattened.
    You can filter items by excluding them from the list.
    Empty lists are okay.
    """
    if asyncio.iscoroutinefunction(map_f):
        _map_f = map_f
    else:
        async def _map_f(_):
            return map_f(_)

    async for _ in aiter:
        try:
            items = await _map_f(_)
            for _ in items:
                yield _
        except Exception:
            logging.exception("unhandled mapping function %s worker exception on %s", map_f, _)
