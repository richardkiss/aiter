import asyncio


def aiter_to_iter(aiter, loop=None):
    """
    Convert an async iterator to a regular iterator by invoking
    run_until_complete repeatedly.
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    underlying_aiter = aiter.__aiter__()
    while True:
        try:
            _ = loop.run_until_complete(underlying_aiter.__anext__())
            yield _
        except StopAsyncIteration:
            break
