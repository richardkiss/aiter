import asyncio
import weakref

from .proxy import proxy_for_instance
from .response import Response
from .typecasting import recast_arguments, recast_to_type
from .RPCMessage import RPCMessage


class RPCStream:
    def __init__(
        self,
        msg_aiter_in,
        async_msg_out_callback,
        rpc_message_class,
        from_simple_types,
        to_simple_types,
        bad_channel_callback=None,
    ):
        """
        msg_aiter_in: yields triple of source, target, msg
        async_msg_out_callback: accepts push of triples of source, target, msg
        msg_for_invocation: turns the invocation into an (opaque) message
        bad_channel_callback: this is called when a reference an invalid channel occurs. For debugging.
        """
        self._msg_aiter_in = msg_aiter_in
        self._async_msg_out_callback = async_msg_out_callback
        self._rpc_message_class = rpc_message_class
        self._from_simple_types = from_simple_types
        self._to_simple_types = to_simple_types
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
            raw_args, raw_kwargs = recast_arguments(annotations, self._to_simple_types, args, kwargs)
            msg = self._rpc_message_class.for_invocation(
                attr_name, raw_args, raw_kwargs, source, channel
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

    async def process_msg_for_obj(self, msg: RPCMessage, obj):
        """
        This method accepts a message and an object, and handles it.
        There are two cases: the message is a request, or the message is a response.
        """
        # check if request vs response
        method_name = msg.method_name()
        if method_name:
            # it's a request

            method = getattr(obj, method_name, None)
            if method is None:
                raise ValueError(f"no method {method} on {obj}")
            annotations = method.__annotations__

            raw_args, raw_kwargs = msg.args_and_kwargs()
            args, kwargs = recast_arguments(
                annotations, self._from_simple_types, raw_args, raw_kwargs
            )
            source = msg.source()
            try:
                r = await method(*args, **kwargs)

                return_type = annotations.get("return")
                simple_r = recast_to_type(r, return_type, self._to_simple_types)

                return self._rpc_message_class.for_response(source, simple_r)
            except Exception as ex:
                return self._rpc_message_class.for_exception(source, str(ex))

        # it's a response, and obj is a Response
        return_type = obj.return_type
        e_text = msg.exception_text()
        if e_text:
            obj.future.set_exception(IOError(e_text))
        else:
            final_r = recast_to_type(msg.response(), return_type, self._from_simple_types)
            obj.future.set_result(final_r)
        return None

    async def _run_inputs(self):
        async for msg in self._msg_aiter_in:
            await self.handle_message(msg)

    async def handle_message(self, msg):
        target = msg.target()
        obj = self._locals_objects_by_channel.get(target)
        if obj is None:
            if self._bad_channel_callback:
                self._bad_channel_callback(target)
                return
        r_msg = await self.process_msg_for_obj(msg, obj)
        if r_msg:
            await self._async_msg_out_callback(r_msg)

    async def await_closed(self):
        """
        Wait for `msg_aiter_in` to stop.
        """
        await self._inputs_task
