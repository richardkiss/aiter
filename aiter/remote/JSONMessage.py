from typing import Any, Optional

import json


class JSONMessage:

    def __init__(self, d):
        self.d = d

    @classmethod
    def deserialize(cls, blob):
        return cls.deserialize_text(blob.decode("utf8"))

    @classmethod
    def deserialize_text(cls, text):
        return cls(json.loads(text))

    def serialize(self):
        return json.dumps(self.d)

    @classmethod
    def for_invocation(cls, method_name, args, kwargs, source, target):
        d = dict(m=method_name)
        if args:
            d["a"] = args
        if kwargs:
            d["k"] = kwargs
        if source is not None:
            d["s"] = source
        if target is not None:
            d["t"] = target

        return cls(d)

    @classmethod
    def for_response(cls, target, r):
        return cls(dict(t=target, r=r))

    @classmethod
    def for_exception(cls, target, text):
        return cls(dict(t=target, e=text))

    def source(self):
        return self.d.get("s")

    def target(self):
        return self.d.get("t", 0)

    def method_name(self) -> Optional[str]:
        return self.d.get("m")

    def exception_text(self) -> Optional[str]:
        return self.d.get("e")

    def response(self) -> Optional[Any]:
        return self.d.get("r")

    def args_and_kwargs(self):
        pair = (self.d.get("a", []), self.d.get("k", {}))
        return pair
