from typing import TYPE_CHECKING, Type, Iterator, Optional, Union, Dict, Iterable
from ..exceptions import RequestError


try:
    import simplejson as json
except ImportError:
    import json


if TYPE_CHECKING:
    from pyrtable.filters.base import BaseFilter
    from pyrtable.record import BaseRecord, RecordQuery


# noinspection PyMethodMayBeStatic
class BaseContext:
    def fetch_single(self, record_cls: Type['BaseRecord'], record_id: str) -> 'BaseRecord':
        import requests
        from pyrtable.connectionmanager import get_connection_manager

        headers = record_cls.get_request_headers()
        url = record_cls.get_url(record_id=record_id)

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
        record = record_cls()
        record.consume_airtable_data(record_data)
        return record

    def fetch_many(self, record_cls: Type['BaseRecord'], record_filter: Optional['BaseFilter'] = None) \
            -> Iterator['BaseRecord']:
        import requests
        from furl import furl
        from pyrtable.connectionmanager import get_connection_manager

        headers = record_cls.get_request_headers()
        f = furl(record_cls.get_url())
        if record_filter:
            filter_by_formula = record_filter.build_formula(record_cls)
            if filter_by_formula:
                f.args['filterByFormula'] = filter_by_formula

        column_names = record_cls.get_column_names()
        f.args['fields[]'] = column_names

        while True:
            with get_connection_manager():
                response = requests.get(f.url, headers=headers)
                if 400 <= response.status_code < 500:
                    error = response.json().get('error', {})
                    error_message = error.get('message', '')
                    error_type = error.get('type', '')

                    raise RequestError(message=error_message, type=error_type)

            response_json = response.json()
            for record_data in response_json.get('records', []):
                record = record_cls()
                record.consume_airtable_data(record_data)
                yield record

            offset = response_json.get('offset')
            if offset is None:
                break
            f.args['offset'] = offset

    def _create(self, record_cls: Type['BaseRecord'], record: 'BaseRecord') -> None:
        import requests
        from pyrtable.connectionmanager import get_connection_manager

        url = record_cls.get_url()
        headers = record_cls.get_request_headers({
            'Content-Type': 'application/json',
        })
        data = {'fields': record.encode_to_airtable()}

        with get_connection_manager():
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if 400 <= response.status_code < 500:
                error = response.json().get('error', {})
                error_message = error.get('message', '')
                error_type = error.get('type', '')

                raise RequestError(message=error_message, type=error_type)

        record.consume_airtable_data(response.json())

    def _update(self, record_cls: Type['BaseRecord'], record: 'BaseRecord') -> None:
        import requests
        from pyrtable.connectionmanager import get_connection_manager

        dirty_fields = record.encode_to_airtable()
        if not dirty_fields:
            return

        url = record_cls.get_url(record.id)
        headers = record_cls.get_request_headers({
            'Content-Type': 'application/json',
        })
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

    def save(self, record_cls: Type['BaseRecord'], record: 'BaseRecord') -> None:
        """
        Save the record to Airtable.
        """
        if record.id is None:
            self._create(record_cls, record)
        else:
            self._update(record_cls, record)

    def delete(self, record_cls: Type['BaseRecord'], record: Union['BaseRecord', str]) -> None:
        import requests
        from pyrtable.connectionmanager import get_connection_manager
        from pyrtable.record import BaseRecord

        if isinstance(record, BaseRecord):
            record_id = record.id
        else:
            record_id = record
            record = None

        url = record_cls.get_url(record_id)
        headers = record_cls.get_request_headers()

        with get_connection_manager():
            response = requests.delete(url, headers=headers)
            if 400 <= response.status_code < 500:
                error = response.json().get('error', {})
                error_message = error.get('message', '')
                error_type = error.get('type', '')

                raise RequestError(message=error_message, type=error_type)

        if record is not None:
            record._id = None
            record._created_timestamp = None
            # delete() does not clear data, but anything that is semantically different from None
            # becomes instantly dirty. That's why we are assigning None to all original values.
            for attr_name, field in record.iter_fields():
                # noinspection PyProtectedMember
                record._orig_fields_values[attr_name] = field.decode_from_airtable(None)


class SimpleCachingContext(BaseContext):
    @staticmethod
    def _build_key(record_cls: Type['BaseRecord'], record_id: str) -> str:
        return '%s:%s' % (record_cls.__name__, record_id)

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
        from pyrtable.record import BaseRecord, RecordQuery

        for arg in args:
            if isinstance(arg, BaseRecord) and arg.id is not None:
                with self._cache_lock:
                    self._cache[self._build_key(arg.__class__, arg.id)] = arg
            elif isinstance(arg, RecordQuery):
                # This will fetch and cache records
                list(arg)
            elif inspect.isclass(arg) and issubclass(arg, BaseRecord):
                list(arg.objects.all())
            else:
                raise ValueError(arg)

    def fetch_single(self, record_cls: Type['BaseRecord'], record_id: str) -> 'BaseRecord':
        if not self._is_cached_class(record_cls):
            return super(SimpleCachingContext, self).fetch_single(record_cls=record_cls, record_id=record_id)

        key = self._build_key(record_cls, record_id)
        with self._cache_lock:
            record = self._cache.get(key)
        if record is not None:
            return record

        record = super(SimpleCachingContext, self).fetch_single(record_cls=record_cls, record_id=record_id)
        with self._cache_lock:
            self._cache[key] = record
        return record

    def fetch_many(self, record_cls: Type['BaseRecord'], record_filter: Optional['BaseFilter'] = None) \
            -> Iterator['BaseRecord']:
        for record in super(SimpleCachingContext, self).fetch_many(record_cls, record_filter):
            if self._is_cached_class(record_cls):
                with self._cache_lock:
                    self._cache[self._build_key(record_cls, record.id)] = record
            yield record

    def save(self, record_cls: Type['BaseRecord'], record: 'BaseRecord') -> None:
        super(SimpleCachingContext, self).save(record_cls, record)
        if self._is_cached_class(record_cls):
            with self._cache_lock:
                self._cache[self._build_key(record_cls, record.id)] = record

    def delete(self, record_cls: Type['BaseRecord'], record: Union['BaseRecord', str]) -> None:
        if self._is_cached_class(record_cls):
            from pyrtable.record import BaseRecord

            if isinstance(record, BaseRecord):
                record_id = record.id
            else:
                record_id = record
            if record_id is not None:
                with self._cache_lock:
                    self._cache.pop(self._build_key(record_cls, record_id), None)

        super(SimpleCachingContext, self).delete(record_cls, record)


__all__ = ['BaseContext', 'SimpleCachingContext']
