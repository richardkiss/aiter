async def flatten_aiter(aiter):
    """
    Take an async iterator that returns lists and return the individual
    elements.
    """
    async for items in aiter:
        try:
            for _ in items:
                yield _
        except Exception:
            pass
