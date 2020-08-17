import asyncio
import weakref

from .proxy import proxy_for_instance
from .response import Response


class RPCStream:
    def __init__(
        self,
        msg_aiter_in,
        async_msg_out_callback,
        msg_for_invocation,
        process_msg_for_obj,
        bad_channel_callback=None,
    ):
        """
        msg_aiter_in: yields triple of source, target, msg
        async_msg_out_callback: accepts push of triples of source, target, msg
        msg_for_invocation: turns the invocation into an (opaque) message
        process_msg_for_obj: async method accepting `obj`, `msg`.
            If `msg` is a response, `obj` is a future that should be set
        bad_channel_callback: this is called when a reference an invalid channel occurs. For debugging.
        """
        self._msg_aiter_in = msg_aiter_in
        self._async_msg_out_callback = async_msg_out_callback
        self._msg_for_invocation = msg_for_invocation
        self._process_msg_for_obj = process_msg_for_obj
        self._bad_channel_callback = bad_channel_callback
        self._next_channel = 0
        self._inputs_task = None
        self._locals_objects_by_channel = weakref.WeakValueDictionary()

    def next_channel(self):
        self._next_channel += 1
        return self._next_channel

    def register_local_obj(self, obj, channel):
        self._locals_objects_by_channel[channel] = obj

    def remote_obj(self, cls, channel):
        async def callback_f(attr_name, args, kwargs, annotations):
            source = self.next_channel()
            future = asyncio.Future()
            return_type = annotations.get("return")
            msg = self._msg_for_invocation(
                attr_name, args, kwargs, annotations, source, channel
            )
            response = Response(future, return_type, msg)
            self.register_local_obj(response, source)
            await self._async_msg_out_callback(msg)
            return await future

        return proxy_for_instance(cls, callback_f)

    def start(self):
        """
        Start the task that fetches requests and generates responses.
        It runs until the `msg_aiter_in` stops.
        """
        if self._inputs_task:
            raise RuntimeError(f"{self} already running")
        self._inputs_task = asyncio.ensure_future(self._run_inputs())

    async def _run_inputs(self):
        async for source, target, msg in self._msg_aiter_in:
            # determine if request vs response
            obj = self._locals_objects_by_channel.get(target)
            if obj is None:
                if self._bad_channel_callback:
                    self._bad_channel_callback(target)
                continue
            msg = await self._process_msg_for_obj(self, msg, obj, source, target)
            if msg:
                await self._async_msg_out_callback(msg)

    async def await_closed(self):
        """
        Wait for `msg_aiter_in` to stop.
        """
        await self._inputs_task
