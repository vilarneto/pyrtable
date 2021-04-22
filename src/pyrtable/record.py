import datetime
import re
from typing import TYPE_CHECKING, Type, Iterator, Optional, Dict, Any, Union, List, Callable, Tuple, Protocol

from ._baseandtable import _BaseAndTableSettableProtocol, _BaseAndTableSettableMixin
from .query import RecordQuery, _QueryableProtocol


try:
    import simplejson as json
except ImportError:
    import json

try:
    import pytz
except ImportError:
    pytz = None

from pyrtable.fields import BaseField


if TYPE_CHECKING:
    pass


class _MetaManager:
    table_tag: str = None
    base_tag: str = None

    def __get__(self, instance, owner):
        if self.table_tag is None:
            meta_class = getattr(owner, 'Meta')
            if meta_class is None:
                raise ValueError('No Meta class defined for class %s' % owner.__name__)

            base_tag = getattr(meta_class, 'base')
            if base_tag is None:
                raise ValueError('Meta class does not contain a "base" field')

            table_tag = getattr(meta_class, 'table')
            if table_tag is None:
                m = re.fullmatch(r'(.+)Record', owner.__name__)
                if not m:
                    raise ValueError(
                        'Meta class does not contain a "table" field,'
                        ' and the table name cannot be inferred from the class name')

                table_tag = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', m.group(1))
                table_tag = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', table_tag).lower()

            self.base_tag = base_tag
            self.table_tag = table_tag

        return self


class _ObjectsManager(_QueryableProtocol, _BaseAndTableSettableProtocol):
    @property
    def base_id(self) -> Optional[str]:
        return self._record_class.get_class_base_id()

    @property
    def table_id(self) -> Optional[str]:
        return self._record_class.get_class_table_id()

    def __init__(self, record_class: Type['BaseRecord']):
        super().__init__()
        self._record_class = record_class

    def all(self) -> RecordQuery:
        # noinspection PyProtectedMember
        record_query_cls: Type[RecordQuery] = self._record_class._get_meta_attr('record_query_class', RecordQuery)
        record_query = record_query_cls(record_class=self._record_class)
        return record_query

    def filter(self, *args, **kwargs) -> RecordQuery:
        return self.all().filter(*args, **kwargs)

    def get(self, record_id: str) -> 'BaseRecord':
        return self.all().get(record_id=record_id)

    def set_base_id(self, base_id: str) -> RecordQuery:
        return self.all().set_base_id(base_id)

    def set_table_id(self, table_id: str) -> RecordQuery:
        return self.all().set_table_id(table_id)


class _ObjectsManagerWrapper:
    _managers = {}

    def __get__(self, instance: 'BaseRecord', owner: Type['BaseRecord']):
        if owner not in _ObjectsManagerWrapper._managers:
            _ObjectsManagerWrapper._managers[owner] = _ObjectsManager(owner)

        return _ObjectsManagerWrapper._managers[owner]


class _BaseRecordProtocol(Protocol):
    """Protocol for type hinting"""
    class Meta:
        api_key: str
        base_id: str
        table_id: str
        record_query_class: Type['RecordQuery']

        get_api_key: Callable[[], str]
        get_base_id: Callable[[], str]
        get_table_id: Callable[[], str]
        get_record_query_class: Callable[[], Type['RecordQuery']]


class BaseRecord(_BaseAndTableSettableMixin, _BaseRecordProtocol):
    _ATTRIBUTE_NOT_SPECIFIED = object()

    _id: Optional[str] = None
    _base_id: Optional[str] = None
    _table_id: Optional[str] = None
    _created_timestamp: Optional[datetime.datetime] = None

    meta = _MetaManager()
    objects = _ObjectsManagerWrapper()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

        for attr_name, field in cls.iter_fields():
            # noinspection PyProtectedMember
            field._install_extra_properties(cls, attr_name)

    @classmethod
    def iter_fields(cls) -> Iterator[Tuple[str, BaseField]]:
        yielded_attrs = set()

        for current_cls in cls.__mro__:
            for attr_name, field in list(current_cls.__dict__.items()):
                if attr_name not in yielded_attrs and isinstance(field, BaseField):
                    yielded_attrs.add(attr_name)
                    yield attr_name, field

    @classmethod
    def get_column_names(cls) -> List[str]:
        return [field.column_name for _, field in cls.iter_fields()
                if field.column_name]

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)

        instance._fields = {}

        for attr_name, field in cls.iter_fields():
            field.attr_name = attr_name
            instance._fields[attr_name] = field
            field._record = instance

            if field.column_name is None:
                field._column_name = attr_name

        return instance

    def __init__(self, _base_id: Optional[str] = None, _table_id: Optional[str] = None, **kwargs):
        super().__init__(base_id=_base_id, table_id=_table_id, record_cls=type(self))
        self._fields_values = {}
        self._orig_fields_values = {}

        for attr_name, field in self.iter_fields():
            self._fields_values[attr_name] = field.decode_from_airtable(None, base_and_table=self)
        self._clear_dirty_fields()

        for key, value in kwargs.items():
            if key not in self._fields:
                TypeError('init() got an unexpected keyword argument %r' % key)
            setattr(self, key, value)

    def _clear_dirty_fields(self):
        for attr_name, field in self.iter_fields():
            self._orig_fields_values[attr_name] = field.clone_value(self._fields_values[attr_name])

    def consume_airtable_data(self, data: Dict[str, Any]):
        data = dict(data)
        self._id = data.pop('id')
        self._created_timestamp = datetime.datetime.strptime(data.pop('createdTime'), '%Y-%m-%dT%H:%M:%S.%fZ')
        if pytz is not None:
            self._created_timestamp = pytz.UTC.localize(self._created_timestamp)

        fields_values: Dict[str, Any] = data.pop('fields')

        for attr_name, field in self.iter_fields():
            if field.column_name is None:
                continue
            value = field.decode_from_airtable(fields_values.get(field.column_name), base_and_table=self)
            self._fields_values[attr_name] = value

        self._clear_dirty_fields()

    @property
    def id(self) -> Optional[str]:
        return self._id

    @property
    def created_timestamp(self) -> Optional[datetime.datetime]:
        return self._created_timestamp

    def delete(self) -> None:
        """
        Delete the record from Airtable.
        """
        from pyrtable.context import get_default_context
        get_default_context().delete(self.__class__, self)

    def save(self) -> None:
        """
        Save the record to Airtable.
        """
        from pyrtable.context import get_default_context
        get_default_context().save(self.__class__, self)

    def encode_to_airtable(self, include_non_dirty_fields=False) -> Dict[str, Any]:
        result = {}

        for attr_name, field in self.iter_fields():
            if field.read_only or field.column_name is None:
                continue

            value = self._fields_values[attr_name]
            if not include_non_dirty_fields \
                    and field.is_same_value(value, self._orig_fields_values[attr_name]):
                continue

            result[field.column_name] = field.encode_to_airtable(value)

        return result

    def normalize_fields(self) -> None:
        for field in self._fields.values():
            if field.normalize is not None:
                if field.skip_normalization_if_filled and getattr(self, field.attr_name):
                    # @TODO Differ False and None if the field is boolean
                    pass
                else:
                    if field.normalize_from_attr_name is not None:
                        value = getattr(self, field.normalize_from_attr_name)
                    else:
                        value = getattr(self, field.attr_name)

                    setattr(self, field.attr_name, field.normalize(value))

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.id)

    @classmethod
    def get_request_headers(cls, defaults=None, base_id: Optional[str] = None) -> Dict[str, str]:
        if not defaults:
            defaults = {}
        result = dict(**defaults)

        if hasattr(cls, 'get_api_key'):
            function = cls.get_api_key

            if base_id is not None:
                import functools
                import inspect

                signature = inspect.signature(function)
                # Can base_id be sent as a keyword argument?
                if 'base_id' in signature.parameters \
                        or any(parameter.kind is inspect.Parameter.VAR_KEYWORD
                               for parameter in signature.parameters.values()):
                    function = functools.partial(function, base_id=base_id)

            result['Authorization'] = 'Bearer %s' % function()
        else:
            result['Authorization'] = 'Bearer %s' % cls._get_meta_attr('api_key')

        return result

    @classmethod
    def _get_meta_attr(cls, attr_name: str, default_value: Any = _ATTRIBUTE_NOT_SPECIFIED) -> Any:
        meta_class = getattr(cls, 'Meta', None)
        if meta_class is not None:
            if hasattr(meta_class, attr_name):
                return getattr(meta_class, attr_name)
            elif hasattr(meta_class, 'get_' + attr_name):
                return getattr(meta_class, 'get_' + attr_name)()

        for base_class in cls.__bases__:
            if issubclass(base_class, BaseRecord):
                parent_attribute_not_specified = object()
                value = base_class._get_meta_attr(attr_name=attr_name,
                                                  default_value=parent_attribute_not_specified)
                if value != parent_attribute_not_specified:
                    return value

        if default_value != BaseRecord._ATTRIBUTE_NOT_SPECIFIED:
            return default_value

        raise AttributeError("'Meta.%s' attribute is not defined for class %r" % (attr_name, cls.__name__))

    @classmethod
    def get_class_base_id(cls) -> str:
        return cls._get_meta_attr('base_id', None)

    @classmethod
    def get_class_table_id(cls) -> str:
        return cls._get_meta_attr('table_id', None)


class APIKeyFromSecretsFileMixin:
    AIRTABLE_SECRETS_FILENAME = 'airtable_secrets.yaml'

    @classmethod
    def get_api_key(cls, base_id=None):
        if not issubclass(cls, BaseRecord):
            raise AttributeError('This is a mixin for BaseRecord subclasses')

        from pyrtable.configutils import load_config_file

        cls: Union[BaseRecord, APIKeyFromSecretsFileMixin]

        if base_id is None:
            base_id = cls.get_class_base_id()
        if base_id is None:
            raise ValueError('Base ID is not set')

        all_api_keys = load_config_file(cls.AIRTABLE_SECRETS_FILENAME)
        api_key = all_api_keys.get(base_id)
        if api_key is None:
            raise KeyError('API key not found in file %r: %r' % (cls.AIRTABLE_SECRETS_FILENAME, api_key))
        return api_key


class TableIDFromClassNameMixin:
    @classmethod
    def get_table_id(cls) -> str:
        if not issubclass(cls, BaseRecord):
            raise AttributeError('This is a mixin for BaseRecord subclasses')

        # Respect Meta.table_id if defined
        table_id = cls._get_meta_attr('table_id', None)
        if table_id is not None:
            return table_id

        m = re.fullmatch(r'(.+)Record', cls.__name__)
        if not m:
            raise AttributeError("Class %r does not have a name that ends with 'Record'")

        table_id = m.group(1)
        table_id = re.sub(r'([a-z])([A-Z])', r'\1 \2', table_id)
        return table_id


__all__ = ['BaseRecord', 'APIKeyFromSecretsFileMixin', 'TableIDFromClassNameMixin']
