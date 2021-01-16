import abc
import collections.abc
from typing import TYPE_CHECKING, Generic, Iterable, Iterator, TypeVar, Type, Optional

from ._baseandtable import _BaseAndTableSettableMixin


if TYPE_CHECKING:
    # PyCharm does not recognise BaseRecord usage -- https://youtrack.jetbrains.com/issue/PY-28634
    from .filters.base import BaseFilter
    from .record import BaseRecord


RT = TypeVar('RT', bound='BaseRecord')


class _QueryableProtocol(Generic[RT], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def all(self) -> '_QueryableProtocol[RT]':
        ...

    @abc.abstractmethod
    def filter(self, *args, **kwargs) -> '_QueryableProtocol[RT]':
        ...


class RecordQuery(_BaseAndTableSettableMixin, Generic[RT], Iterable[RT], collections.abc.Iterable):
    def __init__(self, record_class: Type['BaseRecord'], flt: Optional['BaseFilter'] = None):
        super().__init__(base_id=record_class.get_class_base_id(), table_id=record_class.get_class_table_id())

        self._record_class = record_class
        self._filter = flt

    def all(self) -> 'RecordQuery[RT]':
        return self

    def filter(self, *args, **kwargs) -> 'RecordQuery[RT]':
        from .filters import Q

        if self._filter is None:
            self._filter = Q(*args, **kwargs)
        elif isinstance(self._filter, Q):
            self._filter.extend(*args, **kwargs)
        else:
            self._filter = Q(self._filter, *args, **kwargs)

        return self

    def __iter__(self) -> Iterator[RT]:
        from pyrtable.context import get_default_context
        yield from get_default_context().fetch_many(
            record_cls=self._record_class, base_and_table=self, record_filter=self._filter)


__all__ = ['_QueryableProtocol', 'RecordQuery']
