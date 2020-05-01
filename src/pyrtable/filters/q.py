import re
from typing import TYPE_CHECKING, Type, Dict, Tuple

from .base import BaseFilter
from .raw import *


if TYPE_CHECKING:
    from pyrtable.record import BaseRecord


ALL_FILTERS: Dict[str, Type['BaseFilter']] = {
    '': EqualsFilter,
    'ne': NotEqualsFilter,
    'gt': GreaterThanFilter,
    'lt': LessThanFilter,
    'gte': GreaterThanOrEqualsFilter,
    'lte': LessThanOrEqualsFilter,
    'ge': GreaterThanOrEqualsFilter,
    'le': LessThanOrEqualsFilter,
    'empty': IsEmptyFilter,
    'contains': ContainsFilter,
    'excludes': DoesNotContainFilter,
}


def get_filter(arg_name: str) -> Tuple[Type['BaseFilter'], str]:
    m = re.fullmatch(r'(?P<attr_name>.+)__(?P<operation>[a-z]+)', arg_name)
    if not m:
        return EqualsFilter, arg_name

    operation = m.group('operation')
    if operation not in ALL_FILTERS:
        raise ValueError('Invalid operation "%s"' % operation)

    return ALL_FILTERS[operation], m.group('attr_name')


class Q(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        return self._filter.build_formula(record_class)

    def __init__(self, *args, **kwargs):
        self._filter = AndFilter()
        self.extend(*args, **kwargs)

    def extend(self, *args, **kwargs):
        for key, value in kwargs.items():
            filter_cls, attr_name = get_filter(key)
            self._filter.filters.append(filter_cls(attr_name, value))

        for arg in args:
            if not isinstance(arg, BaseFilter):
                raise ValueError(arg)
            self._filter.filters.append(arg)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._filter)


__all__ = ['Q']
