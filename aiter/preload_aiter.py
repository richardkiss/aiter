from .gated_aiter import gated_aiter


async def preload_aiter(preload_size, aiter):
    """
    This aiter wraps around another aiter, and forces a preloaded
    buffer of the given size.
    """

    gate = gated_aiter(aiter)
    gate.push(preload_size)
    async for _ in gate:
        yield _
        gate.push(1)
    gate.stop()
