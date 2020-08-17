import asyncio

from dataclasses import dataclass
from typing import Any, Type


@dataclass
class Response:
    future: asyncio.Future
    return_type: Type
    invocation_msg: Any
