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
    Has a "preflight" that is called whenever :py:func:`__anext__ <__anext__>` is called.
    The :py:func:`__anext__ <__anext__>` method is wrapped with a semaphore so multiple
    tasks can use the same iterator, and each output will go to only
    one task.

    This is functionally very similar to an :class:`async.Queue <async.Queue>`
    object. It creates an aiter that you can `push` items into.
    Unlike a `Queue` object, you can also invoke :py:func:`stop <stop>`, which will
    raise a `StopAsyncIteration` on the listener's side, allowing for a
    clean exit.

    You'd use this when you want to "turn around" execution, ie. have
    a task that is occasionally invoked (like a hardware interrupt)
    to produce a new event for an aiter.
    """
    def __init__(self, tail=None, next_preflight=None):
        """
        :param next_preflight: called every time `__anext__` is invoked. Intended to
            give the creator a chance to add more elements to the queue, if
            necessary.
        :type next_preflight: a function that takes no arguments

        :param tail: the tail where new objects are pushed into the queue. Used by `fork`
        :type tail: push_aiter_head
        """
        if tail is None:
            tail = asyncio.Future()
            push_aiter_head(tail)
        self._tail = tail
        self._next_preflight = next_preflight
        self._semaphore = asyncio.Semaphore()

    def head(self):
        return self._tail.push_aiter_head

    def push(self, *items):
        """
        Accept one or more item and push them to the end of the
        aiter's queue.
        """
        return self._tail.push_aiter_head.push(*items)

    def stop(self):
        """
        Raise a `StopAsyncIteration` exception on the listener side
        once no more already-queued elements are pending.
        """
        return self._tail.push_aiter_head.stop()

    def __aiter__(self):
        return self

    def fork(self, is_active=True):
        """
        Create and return a clone of this aiter at its current state. This copy
        can be used by a separate task, and it will get the same output.

        You might use this is you have an event stream that has different types
        of events, and you want to write several modules, each of which handles
        a subset of event types. Each module can get a view of the entire stream
        and simply ignore events it's not interested in.

        :type is_active: True or False
        :param is_active: If `False`, this clone is a passive one, that will only
            return elements that have already been requested by at least one active
            clone. You might use this feature for a task that keeps stats on events,
            but it doesn't want to force the events to be removed from because
            a backlog of events might cause flow-control to be invoked.
        """
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
        """
        Return a *synchronous* iterator of elements that are immediately
        available to be consumed without waiting for a task switch.
        """
        tail = self._tail
        try:
            while tail.done():
                _, tail = tail.result()
                yield _
        except asyncio.CancelledError:
            pass

    def is_stopped(self):
        """
        Return a boolean indicating whether or not :py:func:`stop <stop>`
        has been called. Additional elements may still be available.

        :return: whether or not the aiter has been stopped
        :rtype: bool
        """
        return self._tail.cancelled()

    def is_item_available(self):
        """
        Return a boolean indicating whether or not an element is available without
        blocking for a task switch.

        :return: whether or not the aiter has been stopped
        :rtype: bool
        """
        return self.is_len_at_least(1)

    def is_len_at_least(self, n):
        """
        Return a boolean indicating whether or not `n` elements are available without
        blocking for a task switch.

        :type n: int
        :param n: count of items

        :return: True iff n items are available
        :rtype: bool
        """
        for _, item in enumerate(self.available_iter()):
            if _+1 >= n:
                return True
        return False

    def __len__(self):
        """
        :return: number of items immediately available withouth blocking
        :rtype: int
        """

        return sum(1 for _ in self.available_iter())
