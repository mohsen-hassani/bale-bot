from collections import defaultdict
from dataclasses import dataclass, field
from typing import Protocol

from entities import Message


class Subscriber[T](Protocol):
    async def __call__(self, message: Message):
        ...


@dataclass
class Channel[T]:
    subscribers: set[Subscriber[T]] = field(default_factory=set)

    def subscribe(self, subscriber: Subscriber[T]) -> None:
        self.subscribers.add(subscriber)

    def unsubscribe(self, subscriber: Subscriber[T]) -> None:
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)

    async def publish(self, message: Message) -> None:
        for subscriber in self.subscribers:
            await subscriber(message)


@dataclass
class Publisher[T]:
    channels: dict[str, Channel[T]] = field(default_factory=lambda: defaultdict(Channel))

    async def publish(self, channel_name: str, message: Message) -> None:
        await self.channels[channel_name].publish(message)

    def subscribe(self, channel_name: str, subscriber: Subscriber[T]) -> None:
        self.channels[channel_name].subscribe(subscriber)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.channels})"
