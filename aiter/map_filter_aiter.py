import asyncio
import logging

from .flatten_aiter import flatten_aiter
from .map_aiter import map_aiter


def map_filter_aiter(map_f, aiter, worker_count=1):
    """
    Take an async iterator and a map function, and apply the function
    to everything coming out of the iterator before passing it on.
    In this case, the map_f must return a list, which will be flattened.
    Empty lists are okay, so you can filter items by excluding them from the list.

    Note: this simply calls map_aiter, then flatten_aiter.

    :type aiter: async iterator
    :param aiter: an aiter

    :type map_f: a function, regular or async, that accepts a single parameter and returns
        a list (or other iterable)
    :param map_f: the mapping function

    :type worker_count: int
    :param worker_count: the number of worker tasks that pull items out of aiter

    :return: an aiter returning transformed items that have been processed through map_f
    :rtype: an async iterator
    """

    new_aiter = flatten_aiter(map_aiter(map_f, aiter, worker_count))
    return new_aiter
