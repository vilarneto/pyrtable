import abc
from typing import Optional, Protocol


def encode_table_id(table_id: str) -> str:
    import urllib.parse
    return urllib.parse.quote(table_id)


class BaseAndTableProtocol(Protocol):
    """
    Protocol for classes that support base_id and table_id getters and basic read-only methods.
    """

    def get_base_id(self) -> Optional[str]:
        ...

    def get_table_id(self) -> Optional[str]:
        ...

    def build_url(self, record_id: Optional[str] = None) -> str:
        ...

    def ensure_base_and_table_match(self, other: 'BaseAndTableProtocol'):
        ...

    def _validate_base_table_ids(self) -> None:
        ...


class MutableBaseAndTableProtocol(BaseAndTableProtocol):
    """
    Protocol for classes that support base_id and table_id getters & setters and basic read-only methods.
    """

    def set_base_id(self, base_id: str) -> 'MutableBaseAndTableProtocol':
        ...

    def set_table_id(self, table_id: str) -> 'MutableBaseAndTableProtocol':
        ...


class BaseAndTableMethodsMixin(metaclass=abc.ABCMeta):
    """
    Default implementations for :class:`BaseAndTableProtocol` methods.
    """

    _API_ROOT_URL = 'https://api.airtable.com/v0'

    @abc.abstractmethod
    def get_base_id(self) -> Optional[str]:
        ...

    @abc.abstractmethod
    def get_table_id(self) -> Optional[str]:
        ...

    def build_url(self, record_id: Optional[str] = None) -> str:
        self._validate_base_table_ids()

        url = '%s/%s/%s' % (self._API_ROOT_URL, self.get_base_id(), encode_table_id(self.get_table_id()))
        if record_id is not None:
            url += '/%s' % record_id
        return url

    def ensure_base_and_table_match(self, other: 'BaseAndTableProtocol'):
        if self.get_base_id() is not None and other.get_base_id() is not None \
                and self.get_base_id() != other.get_base_id():
            raise ValueError('Base IDs do not match')
        if self.get_table_id() is not None and other.get_table_id() is not None \
                and self.get_table_id() != other.get_table_id():
            raise ValueError('Table IDs do not match')

    def _validate_base_table_ids(self) -> None:
        if self.get_base_id() is None:
            raise ValueError('Base ID is not set')
        if self.get_table_id() is None:
            raise ValueError('Table ID is not set')


class BaseAndTable(BaseAndTableMethodsMixin):
    _base_id: Optional[str]
    _table_id: Optional[str]

    def __init__(self, base_id: Optional[str] = None, table_id: Optional[str] = None):
        self._base_id = base_id
        self._table_id = table_id

    def get_base_id(self) -> Optional[str]:
        return self._base_id

    def get_table_id(self) -> Optional[str]:
        return self._table_id

    def __repr__(self):
        return '%s(base_id=%r, table_id=%r)' % (self.__class__.__name__, self._base_id, self._table_id)


__all__ = ['BaseAndTableProtocol', 'MutableBaseAndTableProtocol', 'BaseAndTableMethodsMixin', 'BaseAndTable']
