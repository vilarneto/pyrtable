from typing import TYPE_CHECKING, Type, Iterator, Optional, Union, Dict, Iterable
from ..exceptions import RequestError


try:
    import simplejson as json
except ImportError:
    import json


if TYPE_CHECKING:
    from pyrtable._baseandtable import _BaseAndTableProtocol
    from pyrtable.filters.base import BaseFilter
    from pyrtable.query import RecordQuery
    from pyrtable.record import BaseRecord


# noinspection PyMethodMayBeStatic
class BaseContext:
    def fetch_single(self, *,
                     record_cls: Type['BaseRecord'],
                     record_id: str,
                     base_and_table: '_BaseAndTableProtocol') \
            -> 'BaseRecord':
        import requests
        from pyrtable.connectionmanager import get_connection_manager

        headers = record_cls.get_request_headers(base_id=base_and_table.base_id)
        url = base_and_table.build_url(record_id=record_id)

        with get_connection_manager():
            response = requests.get(url, headers=headers)
            if 400 <= response.status_code < 500:
                error = response.json().get('error', {})

                if error == 'NOT_FOUND':
                    raise KeyError(record_id)

                error_message = error.get('message', '')
                error_type = error.get('type', '')

                raise RequestError(message=error_message, type=error_type)

        record_data = response.json()
        record = record_cls(_base_id=base_and_table.base_id, _table_id=base_and_table.table_id)
        record.consume_airtable_data(record_data)
        return record

    def fetch_many(self, *,
                   record_cls: Type['BaseRecord'],
                   base_and_table: '_BaseAndTableProtocol',
                   record_filter: Optional['BaseFilter'] = None) \
            -> Iterator['BaseRecord']:
        import urllib.parse
        import requests
        from pyrtable.connectionmanager import get_connection_manager

        headers = record_cls.get_request_headers(base_id=base_and_table.base_id)
        url = base_and_table.build_url()
        parsed_url = urllib.parse.urlparse(url)
        url_query_params = urllib.parse.parse_qsl(parsed_url.query, keep_blank_values=True)

        if record_filter:
            filter_by_formula = record_filter.build_formula(record_cls)
            if filter_by_formula:
                url_query_params.append(('filterByFormula', filter_by_formula))

        column_names = record_cls.get_column_names()
        url_query_params.extend(('fields[]', column_name) for column_name in column_names)

        # noinspection PyProtectedMember
        parsed_url = parsed_url._replace(query=urllib.parse.urlencode(url_query_params))

        while True:
            with get_connection_manager():
                response = requests.get(parsed_url.geturl(), headers=headers)
                if 400 <= response.status_code < 500:
                    error = response.json().get('error', {})
                    error_message = error.get('message', '')
                    error_type = error.get('type', '')

                    raise RequestError(message=error_message, type=error_type)

            response_json = response.json()
            for record_data in response_json.get('records', []):
                record = record_cls(_base_id=base_and_table.base_id, _table_id=base_and_table.table_id)
                record.consume_airtable_data(record_data)
                yield record

            offset = response_json.get('offset')
            if offset is None:
                break

            url_query_params = list(filter(lambda pair: pair[0] != 'offset', url_query_params))
            url_query_params.append(('offset', offset))

            # noinspection PyProtectedMember
            parsed_url = parsed_url._replace(query=urllib.parse.urlencode(url_query_params))

    def _create(self,
                record_cls: Type['BaseRecord'],
                record: 'BaseRecord') -> None:
        import requests
        from pyrtable.connectionmanager import get_connection_manager

        url = record.build_url()
        headers = record_cls.get_request_headers({
            'Content-Type': 'application/json',
        }, base_id=record.base_id)
        data = {'fields': record.encode_to_airtable()}

        with get_connection_manager():
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if 400 <= response.status_code < 500:
                error = response.json().get('error', {})
                error_message = error.get('message', '')
                error_type = error.get('type', '')

                raise RequestError(message=error_message, type=error_type)

        record.consume_airtable_data(response.json())

    def _update(self,
                record_cls: Type['BaseRecord'],
                record: 'BaseRecord') -> None:
        import requests
        from pyrtable.connectionmanager import get_connection_manager

        dirty_fields = record.encode_to_airtable()
        if not dirty_fields:
            return

        url = record.build_url(record_id=record.id)
        headers = record_cls.get_request_headers({
            'Content-Type': 'application/json',
        }, base_id=record.base_id)
        data = {'fields': dirty_fields}

        with get_connection_manager():
            response = requests.patch(url, headers=headers, data=json.dumps(data))
            if 400 <= response.status_code < 500:
                error = response.json().get('error', {})
                error_message = error.get('message', '')
                error_type = error.get('type', '')

                raise RequestError(message=error_message, type=error_type)

        # noinspection PyProtectedMember
        record._clear_dirty_fields()

    def save(self,
             record_cls: Type['BaseRecord'],
             record: 'BaseRecord') -> None:
        """
        Save the record to Airtable.
        """
        if record.id is None:
            self._create(record_cls, record)
        else:
            self._update(record_cls, record)

    def delete_id(self, *,
                  record_cls: Type['BaseRecord'],
                  record_id: str,
                  base_and_table: '_BaseAndTableProtocol') -> None:
        import requests
        from pyrtable.connectionmanager import get_connection_manager

        url = base_and_table.build_url(record_id=record_id)
        headers = record_cls.get_request_headers(base_id=base_and_table.base_id)

        with get_connection_manager():
            response = requests.delete(url, headers=headers)
            if 400 <= response.status_code < 500:
                error = response.json().get('error', {})
                error_message = error.get('message', '')
                error_type = error.get('type', '')

                raise RequestError(message=error_message, type=error_type)

    def delete(self,
               record_cls: Type['BaseRecord'],
               record: 'BaseRecord') -> None:
        if record.id is None:
            return

        self.delete_id(record_cls=record_cls, record_id=record.id, base_and_table=record)

        record._id = None
        record._created_timestamp = None
        # delete() does not clear data, but anything that is semantically different from None
        # becomes instantly dirty. That's why we are assigning None to all original fields values.
        for attr_name, field in record.iter_fields():
            # noinspection PyProtectedMember
            record._orig_fields_values[attr_name] = field.decode_from_airtable(None, base_and_table=record)


class SimpleCachingContext(BaseContext):
    @staticmethod
    def _build_key(record_cls: Type['BaseRecord'], base_and_table: '_BaseAndTableProtocol', record_id: str) -> str:
        # noinspection PyProtectedMember
        base_and_table._validate_base_table_ids()
        return '%s:%s:%s' % (record_cls.__name__, base_and_table.base_id, record_id)

    _cache: Dict[str, 'BaseRecord']

    def __init__(self,
                 allow_classes: Optional[Iterable[Type['BaseRecord']]] = None,
                 exclude_classes: Optional[Iterable[Type['BaseRecord']]] = None):
        import threading

        self._cache = {}
        self._cache_lock = threading.Lock()
        self._allow_classes = set(allow_classes) if allow_classes is not None else None
        self._exclude_classes = set(exclude_classes) if exclude_classes is not None else None

    def _is_cached_class(self, record_cls: Type['BaseRecord']):
        if self._exclude_classes is not None and record_cls in self._exclude_classes:
            return False
        if self._allow_classes is not None:
            return record_cls in self._allow_classes
        return True

    def pre_cache(self, *args: Union['BaseRecord', 'RecordQuery', Type['BaseRecord']]):
        import inspect
        from pyrtable.query import RecordQuery
        from pyrtable.record import BaseRecord

        for arg in args:
            if isinstance(arg, BaseRecord) and arg.id is not None:
                with self._cache_lock:
                    self._cache[self._build_key(arg.__class__, arg, arg.id)] = arg
            elif isinstance(arg, RecordQuery):
                # This will fetch and cache records
                _ = list(arg)
            elif inspect.isclass(arg) and issubclass(arg, BaseRecord):
                # This will fetch and cache records
                _ = list(arg.objects.all())
            else:
                raise ValueError(arg)

    def fetch_single(self, *,
                     record_cls: Type['BaseRecord'],
                     record_id: str,
                     base_and_table: '_BaseAndTableProtocol') -> 'BaseRecord':
        if not self._is_cached_class(record_cls):
            return super(SimpleCachingContext, self).fetch_single(
                record_cls=record_cls, record_id=record_id, base_and_table=base_and_table)

        key = self._build_key(record_cls, base_and_table, record_id)
        with self._cache_lock:
            record = self._cache.get(key)
        if record is not None:
            return record

        record = super(SimpleCachingContext, self).fetch_single(
            record_cls=record_cls, record_id=record_id, base_and_table=base_and_table)
        with self._cache_lock:
            self._cache[key] = record
        return record

    def fetch_many(self, *,
                   record_cls: Type['BaseRecord'],
                   base_and_table: '_BaseAndTableProtocol',
                   record_filter: Optional['BaseFilter'] = None) -> Iterator['BaseRecord']:
        for record in super(SimpleCachingContext, self).fetch_many(
                record_cls=record_cls, base_and_table=base_and_table, record_filter=record_filter):
            if self._is_cached_class(record_cls):
                with self._cache_lock:
                    self._cache[self._build_key(record_cls, record, record.id)] = record
            yield record

    def save(self, record_cls: Type['BaseRecord'], record: 'BaseRecord') -> None:
        super(SimpleCachingContext, self).save(record_cls, record)
        if self._is_cached_class(record_cls):
            with self._cache_lock:
                self._cache[self._build_key(record_cls, record, record.id)] = record

    def delete_id(self, *,
                  record_cls: Type['BaseRecord'],
                  record_id: str,
                  base_and_table: '_BaseAndTableProtocol') -> None:
        if self._is_cached_class(record_cls):
            with self._cache_lock:
                self._cache.pop(self._build_key(record_cls, base_and_table, record_id), None)

        super(SimpleCachingContext, self).delete_id(
            record_cls=record_cls, record_id=record_id, base_and_table=base_and_table)


__all__ = ['BaseContext', 'SimpleCachingContext']
