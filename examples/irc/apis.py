import datetime

from typing import List

from aiter.remote import JSONMessage
from aiter.remote.one_shot import one_shot
from aiter.remote.proxy import Proxy


class MyJSONMessage(JSONMessage):
    @classmethod
    def from_simple_types(cls, v, t, rpc_streamer):
        d = {
            None: lambda a: None,
            bool: lambda a: True if a else False,
            str: lambda a: a,
            int: lambda a: a,
            datetime.datetime: lambda v: datetime.datetime.fromtimestamp(float(v)),
            RoomAPI: lambda v: rpc_streamer.remote_obj(RoomAPI, v),
            MemberAPI: lambda v: rpc_streamer.remote_obj(MemberAPI, v),
        }
        return cls.convert_with_table(v, t, d)

    @classmethod
    def to_simple_types(cls, v, t, rpc_streamer):
        if isinstance(v, Proxy):
            r = rpc_streamer._remote_channels_by_proxy.get(v)
            if r:
                return r
        d = {
            None: lambda a: 0,
            bool: lambda a: 1 if a else 0,
            str: lambda a: a,
            int: lambda a: a,
            datetime.datetime: lambda v: str(v.timestamp()),
            RoomAPI: lambda v: rpc_streamer.register_local_obj(v),
            MemberAPI: lambda v: rpc_streamer.register_local_obj(v),
        }
        return cls.convert_with_table(v, t, d)


class MemberAPI:
    def __init__(self, path):
        self._output = open(path, "a+")

    @one_shot
    async def accept_message(self, msg: str) -> None:
        self._output.write(msg)
        self._output.write("\n")
        self._output.flush()


class RoomAPI:
    def __init__(self, name):
        self._name = name
        self._members = set()

    async def members(self) -> List[MemberAPI]:
        return list(self._members)

    async def join(self, me: MemberAPI) -> None:
        self._members.add(me)

    async def send_msg(self, msg: str) -> None:
        for _ in self._members:
            try:
                await _.accept_message(msg)
            except Exception as ex:
                print(f"oops! {ex}")


class ServerAPI:
    def __init__(self):
        self._rooms = dict()

    async def create_room(self, room_name: str) -> RoomAPI:
        if room_name in self._rooms:
            raise ValueError(f"room {room_name} exists")
        room = self._rooms[room_name] = RoomAPI(room_name)
        return room

    async def room_for_name(self, room_name: str) -> RoomAPI:
        room = self._rooms.get(room_name)
        if room is None:
            return await self.create_room(room_name)
            raise ValueError(f"room {room_name} does not exist")
        return room
