from __future__ import annotations

import collections
from enum import Enum
from typing import TypeVar, MutableSet, Iterator, Callable, Optional, Union, Any, Type, Generic, Iterable


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)


class ValueSet(collections.MutableSet, collections.Iterable, Generic[T]):
    _items: MutableSet[T]

    def __init__(self, other: ValueSet = None, validator: Optional[Callable[[Any], T]] = None):
        if other is not None:
            self._items = set(other._items)
            self._validator = other._validator
        else:
            self._items = set()

        self._validator = validator
        if self._validator is None:
            def validator(value: T) -> T:
                return value

            self._validator = validator

    def add(self, x: T) -> None:
        self._items.add(self._validator(x))

    def discard(self, x: T) -> None:
        self._items.discard(self._validator(x))

    def set(self, iterable: Iterable[T]) -> None:
        self._items = set(self._validator(value) for value in iterable)

    def __contains__(self, x: Any) -> bool:
        return self._items.__contains__(self._validator(x))

    def __len__(self) -> int:
        return self._items.__len__()

    def __iter__(self) -> Iterator[T_co]:
        return self._items.__iter__()

    def __iadd__(self, other: T) -> ValueSet[T]:
        self.add(other)
        return self

    def __isub__(self, other: T) -> ValueSet[T]:
        self.discard(other)
        return self

    def __repr__(self) -> str:
        return self._items.__repr__()


def validator_from_enum(enum_class: Type[Enum]) -> Callable[[Union[str, Enum]], Union[str, Enum]]:
    def validator(value: Union[str, Enum]) -> Union[str, Enum]:
        try:
            return enum_class(value)
        except ValueError:
            return value

    return validator


__all__ = ['ValueSet', 'validator_from_enum']
