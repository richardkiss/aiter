import asyncio


async def join_aiters(aiter_of_aiters):
    """
    Takes an iterator of async iterators and pipe them into a single async iterator.

    This creates a task to monitor the main iterator, plus a task for each active
    iterator that has come out of the main iterator.
    """

    async def aiter_to_next_job(aiter):
        """
        Return two lists: a list of items to yield, and a list of jobs to add to queue.
        """
        try:
            items = [await aiter.__anext__()]
            jobs = [asyncio.ensure_future(aiter_to_next_job(aiter))]
        except StopAsyncIteration:
            items = jobs = []
        return items, jobs

    async def main_aiter_to_next_job(aiter_of_aiters):
        """
        Return two lists: a list of items to yield, and a list of jobs to add to queue.
        """
        try:
            items = []
            new_aiter = await aiter_of_aiters.__anext__()
            jobs = [
                asyncio.ensure_future(aiter_to_next_job(new_aiter.__aiter__())),
                asyncio.ensure_future(main_aiter_to_next_job(aiter_of_aiters))]
        except StopAsyncIteration:
            jobs = []
        return items, jobs

    jobs = set([main_aiter_to_next_job(aiter_of_aiters.__aiter__())])

    while jobs:
        done, jobs = await asyncio.wait(jobs, return_when=asyncio.FIRST_COMPLETED)
        for _ in done:
            new_items, new_jobs = await _
            for _ in new_items:
                yield _
            jobs.update(_ for _ in new_jobs)
