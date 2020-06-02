import re
from enum import Enum


def quote_column_name(column_name: str) -> str:
    return '{%s}' % column_name


def quote_value(value) -> str:
    import datetime

    if isinstance(value, str):
        return '"%s"' % re.sub(r'(["\'\\])', lambda ch: '\\' + ch.group(0), value)
    if isinstance(value, bool):
        return 'TRUE()' if value else 'FALSE()'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Enum):
        return quote_value(value.value)
    if isinstance(value, datetime.datetime):
        return format(value, '"%Y-%m-%dT%H:%M:%S.%fZ"')
    if isinstance(value, datetime.date):
        return format(value, '"%Y-%m-%d"')
    raise ValueError(value)


def airtable_filter_and(*inner_filters) -> str:
    inner_filters = [inner_filter for inner_filter in inner_filters if inner_filter]

    if len(inner_filters) == 0:
        return ''
    if len(inner_filters) == 1:
        return inner_filters[0]
    return 'AND(%s)' % ','.join(inner_filters)


def airtable_filter_or(*inner_filters) -> str:
    inner_filters = [inner_filter for inner_filter in inner_filters if inner_filter]

    if len(inner_filters) == 0:
        return ''
    if len(inner_filters) == 1:
        return inner_filters[0]
    return 'OR(%s)' % ','.join(inner_filters)


def airtable_filter_not(inner_filter) -> str:
    if not inner_filter:
        return 'FALSE()'
    return 'NOT(%s)' % inner_filter


def airtable_filter_equals(column_name, value) -> str:
    return '{column_name}={value}'.format(
        column_name=quote_column_name(column_name), value=quote_value(value))


def airtable_filter_not_equals(column_name, value) -> str:
    return '{column_name}!={value}'.format(
        column_name=quote_column_name(column_name), value=quote_value(value))


def airtable_filter_greater_than(column_name, value) -> str:
    return '{column_name}>{value}'.format(
        column_name=quote_column_name(column_name), value=quote_value(value))


def airtable_filter_less_than(column_name, value) -> str:
    return '{column_name}<{value}'.format(
        column_name=quote_column_name(column_name), value=quote_value(value))


def airtable_filter_greater_than_or_equals(column_name, value) -> str:
    return '{column_name}>={value}'.format(
        column_name=quote_column_name(column_name), value=quote_value(value))


def airtable_filter_less_than_or_equals(column_name, value) -> str:
    return '{column_name}<={value}'.format(
        column_name=quote_column_name(column_name), value=quote_value(value))


def airtable_filter_multiple_select_contains(column_name, value):
    return 'FIND(", "&{value}&", ",", "&{column_name}&", ")>0'.format(
        column_name=quote_column_name(column_name), value=quote_value(value))


def airtable_filter_multiple_select_does_not_contain(column_name, value):
    return 'FIND(", "&{value}&", ",", "&{column_name}&", ")=0'.format(
        column_name=quote_column_name(column_name), value=quote_value(value))


def airtable_filter_multiple_select_is_empty(column_name):
    return 'NOT({column_name})'.format(column_name=quote_column_name(column_name))


def airtable_filter_multiple_select_is_not_empty(column_name):
    return '{column_name}!=""'.format(column_name=quote_column_name(column_name))
