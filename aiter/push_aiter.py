import asyncio


class push_aiter_head:
    def __init__(self, head):
        self._head = head
        self._head.push_aiter_head = self

    def push(self, *items):
        if self._head.cancelled():
            raise ValueError("%s closed" % self)
        for item in items:
            new_head = asyncio.Future()
            new_head.push_aiter_head = self
            self._head.set_result((item, new_head))
            self._head = new_head

    def stop(self):
        head = self._head
        if not head.done():
            head.cancel()

    def is_stopping(self):
        self._skip_to_head()
        return self._head.cancelled()


class push_aiter:
    """
    An asynchronous iterator based on a linked-list.
    Data goes in the head via "push".
    Allows peeking to determine how many elements are ready.
    Can be copied very cheaply by copying the tail.
    Has a "preflight" that is called whenever __anext__ is called.
    The __anext__ method is wrapped with a semaphore so multiple
    tasks can use the same iterator and each will only get an output once.
    """
    def __init__(self, tail=None, next_preflight=None):
        if tail is None:
            tail = asyncio.Future()
            push_aiter_head(tail)
        self._tail = tail
        self._next_preflight = next_preflight
        self._semaphore = asyncio.Semaphore()

    def head(self):
        return self._tail.push_aiter_head

    def push(self, *items):
        return self._tail.push_aiter_head.push(*items)

    def stop(self):
        return self._tail.push_aiter_head.stop()

    def __aiter__(self):
        return self

    def fork(self, is_active=True):
        next_preflight = self._next_preflight if is_active else None
        return self.__class__(tail=self._tail, next_preflight=next_preflight)

    async def __anext__(self):
        async with self._semaphore:
            if self._next_preflight:
                self._next_preflight(self)
            try:
                _, self._tail = await self._tail
                return _
            except asyncio.CancelledError:
                raise StopAsyncIteration

    def available_iter(self):
        tail = self._tail
        try:
            while tail.done():
                _, tail = tail.result()
                yield _
        except asyncio.CancelledError:
            pass

    def is_stopped(self):
        return self._tail.cancelled()

    def is_item_available(self):
        return self.is_len_at_least(1)

    def is_len_at_least(self, n):
        for _, item in enumerate(self.available_iter()):
            if _+1 >= n:
                return True
        return False

    def __len__(self):
        return sum(1 for _ in self.available_iter())
