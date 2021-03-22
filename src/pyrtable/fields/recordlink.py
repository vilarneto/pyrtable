from __future__ import annotations

import collections.abc
from abc import ABCMeta
from typing import TYPE_CHECKING, Optional, Union, Type, List, Iterator, Iterable, Any

from pyrtable._baseandtable import _BaseAndTableProtocol, BaseAndTable
from pyrtable.fields import BaseField


if TYPE_CHECKING:
    from pyrtable.record import BaseRecord


class BaseRecordLinkField(BaseField, metaclass=ABCMeta):
    _linked_class: Union[Type[BaseRecord], str]

    def __init__(self, column_name: str,
                 linked_class: Union[Type[BaseRecord], str],
                 *args, **kwargs):
        from pyrtable.record import BaseRecord

        def fetcher(linked_record_id: str, *, base_and_table: '_BaseAndTableProtocol') -> BaseRecord:
            nonlocal linked_class

            if isinstance(linked_class, str):
                import re

                module_name, class_name = re.fullmatch(r'(.*)\.(.+)', linked_class).groups()
                module = __import__(module_name, fromlist=[class_name])
                linked_class = getattr(module, class_name)

            query = linked_class.objects
            if base_and_table.base_id is not None:
                query = query.set_base_id(base_and_table.base_id)
            if base_and_table.table_id is not None:
                query = query.set_table_id(base_and_table.table_id)
            return query.get(record_id=linked_record_id)

        self._linked_class = linked_class
        self._fetcher = fetcher

        super().__init__(column_name, *args, **kwargs)

    def get_linked_class(self) -> Type[BaseRecord]:
        if isinstance(self._linked_class, str):
            import re

            module_name, class_name = re.fullmatch(r'(.*)\.(.+)', self._linked_class).groups()
            module = __import__(module_name, fromlist=[class_name])
            self._linked_class = getattr(module, class_name)

        return self._linked_class

    def get_linked_base_and_table(self) -> '_BaseAndTableProtocol':
        from pyrtable._baseandtable import BaseAndTable

        linked_class = self.get_linked_class()
        base_id = linked_class._get_meta_attr('base_id', None)
        table_id = linked_class._get_meta_attr('table_id', None)
        return BaseAndTable(base_id, table_id)


class _RecordLink(BaseAndTable):
    _id: Optional[str] = None
    _record: Optional[BaseRecord] = None
    _fetcher = None

    def __init__(self, *,
                 base_and_table: '_BaseAndTableProtocol',
                 other: Optional[_RecordLink] = None,
                 record_id: Optional[str] = None,
                 record: Optional[BaseRecord] = None,
                 fetcher=None):
        super().__init__(base_id=base_and_table.base_id, table_id=base_and_table.table_id)

        if other is not None:
            self._id = other._id
            self._record = other._record
            self._fetcher = other._fetcher

        if record_id is not None:
            self._id = record_id
        if record is not None:
            self._record = record
        if fetcher is not None:
            self._fetcher = fetcher

    @property
    def id(self) -> str:
        if self._record is not None and self._record.id is not None:
            return self._record.id
        if self._id is None:
            raise ValueError('Reference to unsaved or deleted record')
        return self._id

    @property
    def record(self) -> BaseRecord:
        if self._record is None:
            if self._fetcher is None:
                # @TODO Better error message
                raise ValueError("Don't know how to fetch a record - use `fetcher` or `linked_class` attributes")
            self._record = self._fetcher(self._id, base_and_table=self)

        return self._record

    @property
    def has_fetched_record(self):
        return self._record is not None

    def __eq__(self, other):
        if not isinstance(other, _RecordLink):
            return NotImplemented
        if self._id is not None and self._id == other._id:
            return True
        return self._record is not None and self._record is other._record


class _SingleRecordIdLinkProxyField:
    def __init__(self, record_attr_name: str):
        self._record_attr_name = record_attr_name

    def __get__(self, instance, owner: 'BaseField'):
        # noinspection PyProtectedMember
        value = instance._fields_values[self._record_attr_name]
        return value.id if value is not None else None

    def __set__(self, instance, value: Optional[str]):
        if value is None:
            # noinspection PyProtectedMember
            instance._fields_values[self._record_attr_name] = value
            return
        # @TODO Not really that; also, ignore if value does not change
        raise ValueError(value)


class SingleRecordLinkField(BaseRecordLinkField):
    @staticmethod
    def _get_id_attr_name(attr_name: str) -> str:
        return '%s_id' % attr_name

    @classmethod
    def _install_extra_properties(cls, record_cls: Type['BaseRecord'], attr_name: str):
        super()._install_extra_properties(record_cls, attr_name)
        setattr(record_cls, cls._get_id_attr_name(attr_name), _SingleRecordIdLinkProxyField(attr_name))

    def __get__(self, instance, owner: 'BaseRecord') -> Optional['BaseRecord']:
        value = super().__get__(instance, owner)
        return value.record if value is not None else None

    def validate(self, value: Optional[Union[_RecordLink, Iterable[Any]]], base_and_table: '_BaseAndTableProtocol')\
            -> Any:
        from pyrtable.record import BaseRecord

        if isinstance(value, _RecordLink):
            return value
        if isinstance(value, BaseRecord):
            linked_base_and_table = self.get_linked_base_and_table()
            linked_base_and_table.ensure_base_and_table_match(value)
            return _RecordLink(base_and_table=linked_base_and_table, record=value)
        return super().validate(value, base_and_table=base_and_table)

    def clone_value(self, value: Optional[_RecordLink]) -> Optional[_RecordLink]:
        if value is None:
            return None
        return _RecordLink(base_and_table=value, other=value)

    def decode_from_airtable(self, value: Optional[List[str]], base_and_table: '_BaseAndTableProtocol') \
            -> Optional[_RecordLink]:
        if not value:
            return None
        if len(value) > 1:
            raise ValueError('Multiple records returned')

        return _RecordLink(base_and_table=self.get_linked_base_and_table(), record_id=value[0], fetcher=self._fetcher)

    def encode_to_airtable(self, value: _RecordLink) -> Optional[List[str]]:
        if not value:
            return []
        return [value.id]


class _RecordLinkCollection(BaseAndTable, collections.abc.Collection):
    _items: List[_RecordLink]
    _fetcher = None

    def __init__(self, *,
                 base_and_table: '_BaseAndTableProtocol',
                 other: Optional[_RecordLinkCollection] = None,
                 fetcher=None):
        super(_RecordLinkCollection, self).__init__(base_id=base_and_table.base_id, table_id=base_and_table.table_id)

        self._items = []

        if other is not None:
            self.ensure_base_and_table_match(other)
            if fetcher is None:
                fetcher = other._fetcher
        self._fetcher = fetcher

        if other is not None:
            for item in other._items:
                self._items.append(_RecordLink(base_and_table=self, other=item, fetcher=self._fetcher))

    def clear(self) -> None:
        self._items.clear()

    def ids(self) -> Iterator[str]:
        return (item.id for item in self._items)

    def __bool__(self):
        return bool(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __iadd__(self, other: Union[str, 'BaseRecord']):
        from pyrtable.record import BaseRecord

        if isinstance(other, BaseRecord):
            record = other
            self.ensure_base_and_table_match(other)
            record_link = _RecordLink(
                base_and_table=self, record_id=other.id, record=other, fetcher=self._fetcher)
        else:
            record = None
            record_link = _RecordLink(base_and_table=self, record_id=other, fetcher=self._fetcher)

        try:
            existing_index = self._items.index(record_link)
            # Perhaps we have got the missing record?
            if record is not None:
                existing_record_link = self._items[existing_index]
                if not existing_record_link.has_fetched_record:
                    self._items[existing_index] = record_link

        except ValueError:
            self._items.append(record_link)

        return self

    def __isub__(self, other: Union[str, BaseRecord]):
        from pyrtable.record import BaseRecord

        if isinstance(other, BaseRecord):
            self.ensure_base_and_table_match(other)
            record_link = _RecordLink(
                base_and_table=self, record_id=other.id, record=other, fetcher=self._fetcher)
        else:
            record_link = _RecordLink(
                base_and_table=self, record_id=other, fetcher=self._fetcher)

        try:
            self._items.remove(record_link)
        except ValueError:
            pass

        return self

    def __contains__(self, value: object) -> bool:
        return value in self._items

    def __eq__(self, other):
        if not isinstance(other, _RecordLinkCollection):
            return NotImplemented
        return self._items == other._items

    def _iter_ids(self) -> Iterator[Optional[str]]:
        # noinspection PyProtectedMember
        yield from (item._id for item in self._items)

    def __iter__(self) -> Iterator[BaseRecord]:
        for item in self._items:
            yield item.record


class _MultipleRecordIdsLinkProxyField:
    def __init__(self, record_attr_name: str):
        self._record_attr_name = record_attr_name

    def __get__(self, instance, owner: 'BaseField') -> Iterator[str]:
        # noinspection PyProtectedMember
        value = instance._fields_values[self._record_attr_name]
        # noinspection PyProtectedMember
        yield from value._iter_ids()


class MultipleRecordLinkField(BaseRecordLinkField):
    @staticmethod
    def _get_ids_attr_name(attr_name: str) -> str:
        return '%s_ids' % attr_name

    @classmethod
    def _install_extra_properties(cls, record_cls: Type['BaseRecord'], attr_name: str):
        super()._install_extra_properties(record_cls, attr_name)
        setattr(record_cls, cls._get_ids_attr_name(attr_name), _MultipleRecordIdsLinkProxyField(attr_name))

    def validate(self,
                 value: Optional[Union[_RecordLinkCollection, Iterable[Any]]],
                 base_and_table: '_BaseAndTableProtocol') -> Any:
        if isinstance(value, _RecordLinkCollection):
            linked_base_and_table = self.get_linked_base_and_table()
            linked_base_and_table.ensure_base_and_table_match(value)
            return _RecordLinkCollection(base_and_table=linked_base_and_table, other=value)
        if isinstance(value, collections.abc.Iterable):
            result = _RecordLinkCollection(base_and_table=self.get_linked_base_and_table(), fetcher=self._fetcher)
            for record_id in value or []:
                result += record_id
            return result

        return super().validate(value, base_and_table=base_and_table)

    def clone_value(self, value: _RecordLinkCollection) -> _RecordLinkCollection:
        return _RecordLinkCollection(base_and_table=self.get_linked_base_and_table(), other=value)

    def decode_from_airtable(self, value: Optional[List[str]], base_and_table: '_BaseAndTableProtocol') \
            -> _RecordLinkCollection:
        result = _RecordLinkCollection(base_and_table=self.get_linked_base_and_table(), fetcher=self._fetcher)
        for record_id in value or []:
            result += record_id
        return result

    def encode_to_airtable(self, value: _RecordLinkCollection) -> Optional[List[str]]:
        if not value:
            return None
        return list(value.ids())


__all__ = ['SingleRecordLinkField', 'MultipleRecordLinkField']
