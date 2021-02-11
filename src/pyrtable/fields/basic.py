import datetime
from typing import TYPE_CHECKING, Dict, Optional, Union


if TYPE_CHECKING:
    from pyrtable._baseandtable import _BaseAndTableProtocol


try:
    import pytz
except ImportError:
    pytz = None

from pyrtable.fields import BaseField


class StringField(BaseField):
    def decode_from_airtable(self, value: Optional[str], base_and_table: '_BaseAndTableProtocol') -> str:
        return value or ''

    def encode_to_airtable(self, value: Optional[str]) -> Optional[str]:
        return value or None

    def validate(self, value: Optional[str], base_and_table: '_BaseAndTableProtocol') -> str:
        return value or ''


class IntegerField(BaseField):
    def decode_from_airtable(
            self,
            value: Optional[Union[int, Dict]],
            base_and_table: '_BaseAndTableProtocol') -> Optional[int]:
        if value is None:
            return None
        elif isinstance(value, dict):
            if value.get('specialValue') == 'NaN':
                return None
            raise ValueError(value)
        return int(value)

    def encode_to_airtable(self, value: Optional[int]) -> Optional[int]:
        return value


class FloatField(BaseField):
    def decode_from_airtable(
            self,
            value: Optional[Union[float, Dict]],
            base_and_table: '_BaseAndTableProtocol') -> Optional[float]:
        if value is None:
            return None
        elif isinstance(value, dict):
            if value.get('specialValue') == 'NaN':
                import math
                return math.nan
            raise ValueError(value)
        return float(value)

    def encode_to_airtable(self, value: Optional[float]) -> Optional[float]:
        return value


class BooleanField(BaseField):
    def decode_from_airtable(self, value: Optional[bool], base_and_table: '_BaseAndTableProtocol') -> bool:
        return bool(value)

    def encode_to_airtable(self, value: bool) -> Optional[bool]:
        return True if value else None


class DateField(BaseField):
    def decode_from_airtable(self, value: Optional[str], base_and_table: '_BaseAndTableProtocol') \
            -> Optional[datetime.date]:
        if not value:
            return None
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()

    def encode_to_airtable(self, value: Optional[datetime.date]) -> Optional[str]:
        if value is None:
            return None
        return format(value, '%Y-%m-%d')


class DateTimeField(BaseField):
    def decode_from_airtable(self, value, base_and_table: '_BaseAndTableProtocol'):
        if not value:
            return None
        timestamp = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
        if pytz is not None:
            timestamp = pytz.UTC.localize(timestamp)
        return timestamp

    def encode_to_airtable(self, value):
        if value is None:
            return None

        if pytz is not None:
            value = value.astimezone(pytz.UTC)
        elif value.tzinfo is not None:
            import sys
            print('Warning: Using timezone-aware datetime values require the pytz package', file=sys.stderr)

        return format(value, '%Y-%m-%dT%H:%M:%S.%fZ')


__all__ = ['StringField', 'IntegerField', 'FloatField', 'BooleanField', 'DateField', 'DateTimeField']
