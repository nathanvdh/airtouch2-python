from abc import ABC, abstractmethod
from asyncio import Task
from typing import Awaitable, Callable, Coroutine, Protocol, TypeVar


class Serializable(ABC):
    @abstractmethod
    def to_bytes(self) -> bytes:
        pass


SendCoro = Callable[[Serializable], Awaitable[None]]
RecvCoro = Callable[[int], Awaitable[bytes | None]]
Callback = Callable[[], None]
CoroCallback = Callable[[], Awaitable[None]]
TaskCreator = Callable[[Coroutine], Task]


class Publisher(ABC):
    @abstractmethod
    def add_callback(self, callback: Callback) -> Callback:
        """Subscribe 'callback' to info updates. Return a callback that unsubscribes."""
        pass


# dumb thing required to pass containers of implementations as parameters
# to functions that expect containers of interfaces.
PublisherType = TypeVar("PublisherType", bound=Publisher)


def add_callback(callback: Callback, callbacks: list[Callback]) -> Callback:
    callbacks.append(callback)

    def remove_callback() -> None:
        if callback in callbacks:
            callbacks.remove(callback)

    return remove_callback
