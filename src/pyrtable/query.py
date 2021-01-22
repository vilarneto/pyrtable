import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, Iterable, Iterator, TypeVar, Type, Optional, AsyncIterable, AsyncIterator

from ._baseandtable import _BaseAndTableSettableMixin


if TYPE_CHECKING:
    # PyCharm does not recognise BaseRecord usage -- https://youtrack.jetbrains.com/issue/PY-28634
    from .filters.base import BaseFilter
    from .record import BaseRecord


RT = TypeVar('RT', bound='BaseRecord')
QT = TypeVar('QT', bound='RecordQuery')


class _QueryableProtocol(Generic[RT], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def all(self) -> '_QueryableProtocol[RT]':
        ...

    @abc.abstractmethod
    def filter(self, *args, **kwargs) -> '_QueryableProtocol[RT]':
        ...

    @abc.abstractmethod
    async def get(self, record_id: str) -> RT:
        ...


class RecordQuery(_BaseAndTableSettableMixin, Generic[RT, QT], AsyncIterable[RT], _QueryableProtocol[RT],
                  collections.abc.AsyncIterable):
    def __init__(self, record_class: Type['BaseRecord'], flt: Optional['BaseFilter'] = None):
        super().__init__(base_id=record_class.get_class_base_id(), table_id=record_class.get_class_table_id())

        self._record_class = record_class
        self._filter = flt

    def all(self) -> QT:
        return self

    def filter(self, *args, **kwargs) -> QT:
        if not args and not kwargs:
            return self

        from .filters import Q

        if self._filter is None:
            self._filter = Q(*args, **kwargs)
        elif isinstance(self._filter, Q):
            self._filter.extend(*args, **kwargs)
        else:
            self._filter = Q(self._filter, *args, **kwargs)

        return self

    async def get(self, *, record_id: str) -> RT:
        from pyrtable.context import get_default_context

        if self._filter is not None:
            raise ValueError('Currently get() is not compatible with filters applied')

        return await get_default_context().fetch_single(
            record_cls=self._record_class, record_id=record_id, base_and_table=self)

    async def __aiter__(self) -> AsyncIterator[RT]:
        from pyrtable.context import get_default_context

        async for record in get_default_context().fetch_many(
                record_cls=self._record_class, base_and_table=self, record_filter=self._filter):
            yield record


__all__ = ['_QueryableProtocol', 'RecordQuery']
