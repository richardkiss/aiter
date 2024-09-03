import asyncio


def run(f):
    return asyncio.new_event_loop().run_until_complete(f)


async def get_n(aiter, n=0):
    """
    Get n items.
    """
    r = []
    count = 0
    async for _ in aiter:
        r.append(_)
        count += 1
        if count >= n and n != 0:
            break
    return r
