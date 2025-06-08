"""
Conversation Navigator
---------------------
Iterates through conversation URLs from a list or API source.
"""

from typing import Iterable, Iterator


class ConversationNavigator:
    """Cycle through conversation URLs."""

    def __init__(self, urls: Iterable[str]):
        self._urls = iter(urls)

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        return next(self._urls)
