async def azip(*aiters):
    """
    async version of zip
    This function takes a list of async iterators and returns a single async iterator
    that yields tuples of elements.

    Obviously this iterator advances as slow its slowest component.

    example:
        async for a, b, c in azip(aiter1, aiter2, aiter3):
            print(a, b, c)
    """
    anext_tuple = tuple([_.__aiter__() for _ in aiters])
    while True:
        try:
            next_tuple = tuple([await _.__anext__() for _ in anext_tuple])
        except StopAsyncIteration:
            break
        yield next_tuple
