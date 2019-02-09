async def iter_to_aiter(iter):
    """
    This converts a regular iterator to an async iterator
    """
    for _ in iter:
        yield _
