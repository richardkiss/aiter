import asyncio

from typing import Awaitable, List, Set, Tuple, TypeVar

T = TypeVar("T")

AwaitAwait = Awaitable[Awaitable[T]]
ItemsJobsPair = Tuple[List[T], List[Awaitable["ItemsJobsPair"]]]


async def join_aiters[T](aiter_of_aiters: AwaitAwait[T]) -> Awaitable[T]:
    """
    This wrapper takes an aiter of aiters and pipe the items coming out of all of them into a
    single aiter.

    :type aiter_of_aiters: async iterator
    :param aiter_of_aiters: an aiter that yields aiters

    :return: an aiter returning elements that come from any of the underlying aiters
    :rtype: async iterator
    """

    async def _aiter_to_next_job(aiter: Awaitable[T]) -> ItemsJobsPair:
        """
        Return two lists: a list of items to yield, and a list of jobs to add to queue.
        """
        try:
            items: List[T] = [await aiter.__anext__()]
            jobs: List[asyncio.Task] = [
                asyncio.ensure_future(_aiter_to_next_job(aiter))
            ]
        except StopAsyncIteration:
            items = jobs = []
        return items, jobs

    async def _main_aiter_to_next_job(aiter_of_aiters: AwaitAwait[T]) -> ItemsJobsPair:
        """
        Return two lists: a list of items to yield, and a list of jobs to add to queue.
        """
        items: List[T] = []
        try:
            new_aiter: Awaitable[T] = await aiter_of_aiters.__anext__()
            jobs: List[asyncio.Task] = [
                asyncio.ensure_future(_aiter_to_next_job(new_aiter.__aiter__())),
                asyncio.ensure_future(_main_aiter_to_next_job(aiter_of_aiters)),
            ]
        except StopAsyncIteration:
            jobs = []
        return items, jobs

    new_coroutine: Awaitable[ItemsJobsPair] = _main_aiter_to_next_job(
        aiter_of_aiters.__aiter__()
    )
    new_task: asyncio.Task = asyncio.ensure_future(new_coroutine)
    jobs: Set[asyncio.Task] = set([new_task])

    while jobs:
        done, jobs = await asyncio.wait(jobs, return_when=asyncio.FIRST_COMPLETED)
        for _ in done:
            new_items, new_jobs = await _
            for _ in new_items:
                yield _
            jobs.update(_ for _ in new_jobs)
