import asyncio


class Latch[T]:
    """
    The simplest core object that manages the following states:

    - AWAITING_PUSH
      - pull => wait for AWAITING_PULL
      - push => AWAITING_PULL
      - close => CLOSED
    - AWAITING_PULL
      - push => wait for AWAITING_PUSH
      - pull => AWAITING_PUSH
      - close => AWAITING_LAST_PULL
    - AWAITING_LAST_PULL
      - push => fail
      - pull => CLOSED
      - close => fail
    - CLOSED (pushes and pulls fail)
      - push => fail
      - pull => fail
      - close => fail
    """

    _push_ready_event: asyncio.Event
    _pull_ready_event: asyncio.Event
    _is_open: bool
    _item: T

    def __init__(self):
        self._push_ready_event = asyncio.Event()
        self._pull_ready_event = asyncio.Event()
        self._is_open = True

    def close(self) -> None:
        """
        Stop accepting new items.
        """
        if not self._is_open:
            raise ValueError("already closed")
        self._is_open = False
        self._push_ready_event.set()
        self._pull_ready_event.set()

    async def push(self, item: T) -> None:
        """
        Push an item
        """
        await self._push_ready_event.wait()
        if not self._is_open:
            raise ValueError("closed")
        self._item: T = item
        self._push_ready_event.clear()
        self._pull_ready_event.set()

    async def pull(self) -> T:
        if self._is_open or hasattr(self, "_item"):
            self._push_ready_event.set()
            await self._pull_ready_event.wait()
            item = self._item
            del self._item
            self._pull_ready_event.clear()
            return item
        else:
            raise StopAsyncIteration
