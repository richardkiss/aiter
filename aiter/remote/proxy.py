def proxy_for_instance(cls, callback_f):
    """
    Call the callback_f with `attr_name`, `args`, `kwargs`, `annotations`.
    """

    class Proxy:
        """
        This class is a "proxy" object that turns all its attributes
        into callables that simply invoke "callback_f" with the name
        of the attribute and the given context.

        This is so you can create a proxy, then do something like

        proxy.call_my_function(foo, bar)

        and it will actually call

        callback_f("call_my_function", context, foo, bar)

        so the callback_f can actually start a remote procedure call.
        """

        @classmethod
        def __getattribute__(self, attr_name):
            async def invoke(*args, **kwargs):
                # look in the class for the attribute
                # make sure it's an async function
                # collect up the metadata with types to build args, kwargs with `Argument`
                attribute = getattr(cls, attr_name, None)
                if attribute is None:
                    raise AttributeError(f"bad attribute {attr_name}")
                annotations = attribute.__annotations__
                return await callback_f(attr_name, args, kwargs, annotations)

            return invoke

    return Proxy()
