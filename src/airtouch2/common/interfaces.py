from abc import ABC, abstractmethod
from asyncio import Task
from typing import Awaitable, Callable, Coroutine


class Serializable(ABC):
    @abstractmethod
    def to_bytes(self) -> bytes:
        pass


SendCoro = Callable[[Serializable], Awaitable[None]]
RecvCoro = Callable[[int], Awaitable[bytes | None]]
Callback = Callable[[], None]
CoroCallback = Callable[[], Awaitable[None]]
TaskCreator = Callable[[Coroutine], Task]
