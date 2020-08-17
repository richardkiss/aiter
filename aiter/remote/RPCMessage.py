from typing import Any, Optional


class RPCMessage:
    @classmethod
    def deserialize(cls, blob):
        pass

    def serialize(self):
        pass

    @classmethod
    def for_invocation(cls, method_name, args, kwargs, source, target):
        pass

    @classmethod
    def for_response(cls, target, r):
        pass

    @classmethod
    def for_exception(cls, target, text):
        pass

    def source(self):
        pass

    def target(self):
        pass

    def exception_text(self) -> Optional[str]:
        pass

    def response(self) -> Optional[Any]:
        pass

    def method_name(self) -> Optional[str]:
        # return None if it's not a request
        pass

    def args_and_kwargs(self):
        pass
