import datetime
import re
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional, Protocol, Tuple

from ._baseandtable import BaseAndTableMethodsMixin, BaseAndTableProtocol
from .query import RecordQuery

try:
    import simplejson as json
except ImportError:
    import json

try:
    import zoneinfo
except ImportError:
    try:
        # noinspection PyPackageRequirements
        from backports import zoneinfo
    except ImportError:
        zoneinfo = None

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


class _BaseRecordProtocol(Protocol):
    """
    Protocol for :class:`BaseRecord` type hinting.
    """
    class Meta:
        api_key: str
        base_id: str
        table_id: str

        get_api_key: Callable[[], str]
        get_base_id: Callable[[], str]
        get_table_id: Callable[[], str]


class BaseRecord(BaseAndTableMethodsMixin, _BaseRecordProtocol):
    """
    Base class for all table records.
    """

    def get_base_id(self) -> Optional[str]:
        return self.get_class_base_id() if self._base_id is None else self._base_id

    def get_table_id(self) -> Optional[str]:
        return self.get_class_table_id() if self._table_id is None else self._table_id

    _ATTRIBUTE_NOT_SPECIFIED = object()

    _base_id: Optional[str] = None
    _table_id: Optional[str] = None
    _id: Optional[str] = None
    _created_timestamp: Optional[datetime.datetime] = None

    meta = _MetaManager()
    objects = RecordQuery()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

        for attr_name, field in cls.iter_fields():
            # noinspection PyProtectedMember
            field._install_extra_properties(cls, attr_name)

        for attr_name, record_query in cls._iter_record_query_attrs():
            # noinspection PyProtectedMember
            if record_query._record_class is None:
                record_query._record_class = cls
            elif record_query._record_class is not cls:
                import copy
                record_query = copy.copy(record_query)
                record_query._record_class = cls
                setattr(cls, attr_name, record_query)

        # Check deprecated mechanism
        record_query_cls = cls._get_meta_attr('record_query_class', None)
        if record_query_cls is not None:
            import logging
            logger = logging.getLogger('pyrtable')
            logger.warning('record_query_class meta attributes are deprecated and will be ignored.')

    @classmethod
    def _iter_record_query_attrs(cls) -> Iterator[Tuple[str, RecordQuery]]:
        yielded_attrs = set()
        yielded_attr_names = set()

        for current_cls in cls.__mro__:
            for attr_name, attr in list(current_cls.__dict__.items()):
                if isinstance(attr, RecordQuery) and attr not in yielded_attrs and attr_name not in yielded_attr_names:
                    yielded_attrs.add(attr)
                    yielded_attr_names.add(attr_name)
                    yield attr_name, attr

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
            if attr_name in ('id', 'created_timestamp'):
                raise AttributeError(f'"{attr_name}" is a reserved field name and cannot be used')
            field.attr_name = attr_name
            instance._fields[attr_name] = field
            field._record = instance

            if field.column_name is None:
                field._column_name = attr_name

        return instance

    def __init__(self, _base_id: Optional[str] = None, _table_id: Optional[str] = None, **kwargs):
        super().__init__()

        self._base_id = _base_id
        self._table_id = _table_id
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
        """
        Update field values of this record from a dictionary of raw data retrieved from the Airtable server.
        """

        data = dict(data)
        self._id = data.pop('id')
        self._created_timestamp = datetime.datetime.strptime(data.pop('createdTime'), '%Y-%m-%dT%H:%M:%S.%fZ')
        if zoneinfo is not None:
            self._created_timestamp = self._created_timestamp.replace(tzinfo=zoneinfo.ZoneInfo('UTC'))

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
        Delete this record from Airtable.
        """

        from pyrtable.context import get_default_context
        get_default_context().delete(self.__class__, self)

    def save(self) -> None:
        """
        Save this record to Airtable.
        """

        from pyrtable.context import get_default_context
        get_default_context().save(self.__class__, self)

    def encode_to_airtable(self, include_non_dirty_fields=False) -> Dict[str, Any]:
        """
        Build a dictionary of field values ready to be sent to creation/update at the Airtable server.

        :param include_non_dirty_fields: If `True` then all fields will be included in the dictionary; if `False` then
         only fields changed from the last server operation are included (possibly resulting in an empty dictionary).
        :result: The dictionary of raw field values.
        """

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
        result['Authorization'] = 'Bearer %s' % cls._get_api_key(base_id=base_id)

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
    def _get_api_key(cls, base_id: str) -> str:
        import functools
        import inspect

        for base_cls in inspect.getmro(cls):
            if hasattr(base_cls, 'get_api_key'):
                function = base_cls.get_api_key

                signature = inspect.signature(function)
                # Can base_id be sent as a keyword argument?
                if 'base_id' in signature.parameters \
                        or any(parameter.kind is inspect.Parameter.VAR_KEYWORD
                               for parameter in signature.parameters.values()):
                    function = functools.partial(function, base_id=base_id)

                result = function()
                if result is not None:
                    return result

        api_key = cls._get_meta_attr('api_key', default_value=None)
        if api_key is None:
            if base_id is None:
                raise ValueError('Cannot find a default Airtable API Key')
            else:
                raise KeyError('Cannot find an Airtable API Key for base_id=%s' % base_id)

        return api_key

    @classmethod
    def get_class_base_id(cls) -> str:
        return cls._get_meta_attr('base_id', None)

    @classmethod
    def get_class_table_id(cls) -> str:
        return cls._get_meta_attr('table_id', None)


class APIKeyFromEnvMixin:
    """
    Mixin to return the Airtable API Key from the AIRTABLE_API_KEY environment variable.
    """

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        import os
        return os.getenv('AIRTABLE_API_KEY') or None


class APIKeyFromSecretsFileMixin:
    """
    Mixin to return the Airtable API Key from a secrets file.

    This secrets file is a YAML file containing a top-level dictionary whose keys are the base IDs and values are
    corresponding API keys.
    """

    AIRTABLE_SECRETS_FILENAME = 'airtable_secrets.yaml'

    @classmethod
    def get_api_key(cls, base_id: str):
        import os

        from pyrtable.configutils import load_config_file

        airtable_secrets_filename = os.getenv('AIRTABLE_SECRETS_FILENAME')
        if not airtable_secrets_filename:
            airtable_secrets_filename = cls.AIRTABLE_SECRETS_FILENAME

        all_api_keys = load_config_file(airtable_secrets_filename)
        return all_api_keys.get(base_id)


class TableIDFromClassNameMixin:
    @classmethod
    def get_table_id(cls) -> str:
        if not issubclass(cls, BaseRecord):
            raise AttributeError('This is a mixin for BaseRecord subclasses')

        # Respect Meta.get_table_id() if defined
        table_id = cls._get_meta_attr('table_id', None)
        if table_id is not None:
            return table_id

        m = re.fullmatch(r'(.+)Record', cls.__name__)
        if not m:
            raise AttributeError("Class %r does not have a name that ends with 'Record'")

        table_id = m.group(1)
        table_id = re.sub(r'([a-z])([A-Z])', r'\1 \2', table_id)
        return table_id


__all__ = ['BaseRecord', 'APIKeyFromEnvMixin', 'APIKeyFromSecretsFileMixin', 'TableIDFromClassNameMixin']
