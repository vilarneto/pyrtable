import collections.abc
from typing import TYPE_CHECKING, Generic, Iterable, Iterator, TypeVar, Type, Optional

from ._baseandtable import _BaseAndTableSettableProtocol, BaseAndTable


if TYPE_CHECKING:
    from .filters.base import BaseFilter
    from .record import BaseRecord


RT = TypeVar('RT', bound='BaseRecord')
QT = TypeVar('QT', bound='RecordQuery')


class RecordQuery(BaseAndTable, Generic[RT, QT], Iterable[RT],
                  collections.abc.Iterable, _BaseAndTableSettableProtocol):
    """
    A (potentially under construction) query for records in a table. Also represents the starting point for queries
    to be made over a :class:`BaseRecord` derived class, exposed through the `objects` class attribute.
    """
    def set_base_id(self, base_id: str) -> 'QT':
        """
        Change the query's base ID.

        :return: The resulting query.
        """
        result = self._shallow_copy()
        result._base_id = base_id
        return result

    def set_table_id(self, table_id: str) -> 'QT':
        """
        Change the query's table ID.

        :return: The resulting query.
        """
        result = self._shallow_copy()
        result._table_id = table_id
        return result

    _record_class: Type['BaseRecord']
    _initialised = False
    _is_empty_query = False

    def __init__(self, record_class: Type['BaseRecord'], flt: Optional['BaseFilter'] = None):
        super().__init__(base_id=record_class.get_class_base_id(), table_id=record_class.get_class_table_id())

        self._record_class = record_class
        self._filter = flt

    def _shallow_copy(self) -> QT:
        import copy
        result = copy.copy(self)
        return result

    def _shallow_copy_and_initialise(self) -> QT:
        result = self._shallow_copy()
        result._initialised = True
        return result

    def all(self) -> QT:
        """
        Return a query for all records, given that they are not filtered out by other criteria.

        :return: The resulting query.
        """
        if self._initialised:
            return self
        return self._shallow_copy_and_initialise()

    def none(self) -> QT:
        """
        Return an empty query. No server communication is needed to execute this query.

        :return: The resulting query.
        """
        if self._is_empty_query:
            return self
        result = self._shallow_copy_and_initialise()
        result._is_empty_query = True
        return result

    def filter(self, *args, **kwargs) -> QT:
        """
        Return a query that will respect the criteria given as arguments.

        :return: The resulting query.
        """
        if not args and not kwargs:
            return self.all()

        from .filters import Q

        result = self._shallow_copy_and_initialise()

        if result._filter is None:
            result._filter = Q(*args, **kwargs)
        elif isinstance(result._filter, Q):
            result._filter.extend(*args, **kwargs)
        else:
            result._filter = Q(result._filter, *args, **kwargs)

        return result

    def get(self, record_id: str) -> RT:
        """
        Return a single record with given identifier, if it exists in the table.

        :return: The matching record.
        :raises KeyError: if no record matches the given record ID.
        :raises ValueError: if filters were applied (currently this is not supported).
        """
        from pyrtable.context import get_default_context

        # Trivial implementation for Record.objects.none().get(...)
        if self._is_empty_query:
            raise KeyError(record_id)

        if self._filter is not None:
            raise ValueError('Currently get() is not compatible with filters applied')

        return get_default_context().fetch_single(
            record_cls=self._record_class, record_id=record_id, base_and_table=self)

    def __iter__(self) -> Iterator[RT]:
        if not self._initialised:
            raise ValueError('Query is not initialised. Use .all(), .filter() or .none() to initialise it.')

        if self._is_empty_query:
            return

        from pyrtable.context import get_default_context
        yield from get_default_context().fetch_many(
            record_cls=self._record_class, base_and_table=self, record_filter=self._filter)


__all__ = ['RecordQuery']
