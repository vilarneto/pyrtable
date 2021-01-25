import abc
from typing import TYPE_CHECKING, Optional, Type, Protocol


if TYPE_CHECKING:
    from .record import BaseRecord


def encode_table_id(table_id: str) -> str:
    import urllib.parse
    return urllib.parse.quote(table_id)


class _BaseAndTableProtocol(Protocol, metaclass=abc.ABCMeta):
    _API_ROOT_URL = 'https://api.airtable.com/v0'

    @property
    @abc.abstractmethod
    def base_id(self) -> Optional[str]:
        ...

    @property
    @abc.abstractmethod
    def table_id(self) -> Optional[str]:
        ...

    def build_url(self, record_id: Optional[str] = None) -> str:
        self._validate_base_table_ids()

        url = '%s/%s/%s' % (self._API_ROOT_URL, self.base_id, encode_table_id(self.table_id))
        if record_id is not None:
            url += '/%s' % record_id
        return url

    def ensure_base_and_table_match(self, other: '_BaseAndTableProtocol'):
        if self.base_id is not None and other.base_id is not None and self.base_id != other.base_id:
            raise ValueError('Base IDs do not match')
        if self.table_id is not None and other.table_id is not None and self.table_id != other.table_id:
            raise ValueError('Table IDs do not match')

    def _validate_base_table_ids(self) -> None:
        if self.base_id is None:
            raise ValueError('Base ID is not set')
        if self.table_id is None:
            raise ValueError('Table ID is not set')


class _BaseAndTableSettableProtocol(_BaseAndTableProtocol, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def set_base_id(self, base_id: str) -> '_BaseAndTableSettableMixin':
        ...

    @abc.abstractmethod
    def set_table_id(self, table_id: str) -> '_BaseAndTableSettableMixin':
        ...


class _BaseAndTableSettableMixin(_BaseAndTableSettableProtocol):
    def set_base_id(self, base_id: str) -> '_BaseAndTableSettableMixin':
        self._base_id = base_id
        return self

    def set_table_id(self, table_id: str) -> '_BaseAndTableSettableMixin':
        self._table_id = table_id
        return self

    @property
    def base_id(self) -> Optional[str]:
        return self._base_id

    @property
    def table_id(self) -> Optional[str]:
        return self._table_id

    _base_id: Optional[str]
    _table_id: Optional[str]

    def __init__(self,
                 record_cls: Optional[Type['BaseRecord']] = None,
                 base_id: Optional[str] = None,
                 table_id: Optional[str] = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._base_id = base_id
        if self._base_id is None and record_cls is not None:
            self._base_id = record_cls.get_class_base_id()
        self._table_id = table_id
        if self._table_id is None and record_cls is not None:
            self._table_id = record_cls.get_class_table_id()


class BaseAndTable(_BaseAndTableProtocol):
    _base_id: Optional[str]
    _table_id: Optional[str]

    def __init__(self, base_id: Optional[str] = None, table_id: Optional[str] = None):
        self._base_id = base_id
        self._table_id = table_id

    @property
    def base_id(self) -> Optional[str]:
        return self._base_id

    @property
    def table_id(self) -> Optional[str]:
        return self._table_id


__all__ = ['_BaseAndTableProtocol', '_BaseAndTableSettableProtocol', '_BaseAndTableSettableMixin', 'BaseAndTable']
