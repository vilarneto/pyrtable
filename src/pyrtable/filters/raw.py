from typing import Type, List, Any, TYPE_CHECKING

from .base import BaseFilter


if TYPE_CHECKING:
    from pyrtable.record import BaseRecord


class TrueFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        return 'TRUE()'

    def __repr__(self):
        return 'TRUE()'


class FalseFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        return 'FALSE()'

    def __repr__(self):
        return 'FALSE()'


class NotFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        if isinstance(self.filter, TrueFilter):
            return FalseFilter().build_formula(record_class=record_class)
        if isinstance(self.filter, FalseFilter):
            return TrueFilter().build_formula(record_class=record_class)

        from pyrtable.filterutils import airtable_filter_not

        if isinstance(self.filter, NotFilter):
            return self.filter.filter.build_formula(record_class)
        return airtable_filter_not(self.filter.build_formula(record_class))

    def __init__(self, flt: BaseFilter):
        self.filter = flt

    def __repr__(self):
        return 'NOT(%r)' % self.filter


class AndFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        if any(isinstance(flt, FalseFilter) for flt in self.filters):
            return FalseFilter().build_formula(record_class=record_class)

        from pyrtable.filterutils import airtable_filter_and
        return airtable_filter_and(*(flt.build_formula(record_class) for flt in self.filters))

    def __init__(self, *filters: BaseFilter):
        self.filters: List[BaseFilter] = []

        for flt in filters:
            if isinstance(flt, AndFilter):
                self.filters.extend(flt.filters)
            else:
                self.filters.append(flt)

    def __repr__(self):
        return ' & '.join(repr(flt) for flt in self.filters)


class OrFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        if any(isinstance(flt, TrueFilter) for flt in self.filters):
            return TrueFilter().build_formula(record_class=record_class)

        from pyrtable.filterutils import airtable_filter_or
        return airtable_filter_or(*(flt.build_formula(record_class) for flt in self.filters))

    def __init__(self, *filters: BaseFilter):
        self.filters: List[BaseFilter] = []

        for flt in filters:
            if isinstance(flt, OrFilter):
                self.filters.extend(flt.filters)
            else:
                self.filters.append(flt)

    def __repr__(self):
        return ' | '.join(repr(flt) for flt in self.filters)


class EqualsFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        from pyrtable.filterutils import quote_column_name, airtable_filter_equals
        from pyrtable.fields import BooleanField

        field = self.get_field_object(record_class, self.attr_name)

        if isinstance(field, BooleanField):
            if self.value:
                return '(%s)' % quote_column_name(field.column_name)
            else:
                return 'NOT(%s)' % quote_column_name(field.column_name)

        return airtable_filter_equals(column_name=field.column_name, value=self.value)

    def __init__(self, attr_name: str, value: Any):
        self.attr_name = attr_name
        self.value = value

    def __repr__(self):
        return '(.%s = %r)' % (self.attr_name, self.value)


class NotEqualsFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        from pyrtable.filterutils import airtable_filter_not_equals
        return airtable_filter_not_equals(column_name=self.get_column_name(record_class, self.attr_name),
                                          value=self.value)

    def __init__(self, attr_name: str, value: Any):
        self.attr_name = attr_name
        self.value = value

    def __repr__(self):
        return '(.%s != %r)' % (self.attr_name, self.value)


class GreaterThanFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        from pyrtable.filterutils import airtable_filter_greater_than
        return airtable_filter_greater_than(
            column_name=self.get_column_name(record_class, self.attr_name),
            value=self.value)

    def __init__(self, attr_name: str, value: Any):
        self.attr_name = attr_name
        self.value = value

    def __repr__(self):
        return '(.%s > %r)' % (self.attr_name, self.value)


class LessThanFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        from pyrtable.filterutils import airtable_filter_less_than
        return airtable_filter_less_than(
            column_name=self.get_column_name(record_class, self.attr_name),
            value=self.value)

    def __init__(self, attr_name: str, value: Any):
        self.attr_name = attr_name
        self.value = value

    def __repr__(self):
        return '(.%s < %r)' % (self.attr_name, self.value)


class GreaterThanOrEqualsFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        from pyrtable.filterutils import airtable_filter_greater_than_or_equals
        return airtable_filter_greater_than_or_equals(
            column_name=self.get_column_name(record_class, self.attr_name),
            value=self.value)

    def __init__(self, attr_name: str, value: Any):
        self.attr_name = attr_name
        self.value = value

    def __repr__(self):
        return '(.%s >= %r)' % (self.attr_name, self.value)


class LessThanOrEqualsFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        from pyrtable.filterutils import airtable_filter_less_than_or_equals
        return airtable_filter_less_than_or_equals(
            column_name=self.get_column_name(record_class, self.attr_name),
            value=self.value)

    def __init__(self, attr_name: str, value: Any):
        self.attr_name = attr_name
        self.value = value

    def __repr__(self):
        return '(.%s <= %r)' % (self.attr_name, self.value)


class IsEmptyFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        column_name = self.get_column_name(record_class, self.attr_name)
        if self.value:
            from pyrtable.filterutils import airtable_filter_multiple_select_is_empty
            return airtable_filter_multiple_select_is_empty(column_name=column_name)
        else:
            from pyrtable.filterutils import airtable_filter_multiple_select_is_not_empty
            return airtable_filter_multiple_select_is_not_empty(column_name=column_name)

    def __init__(self, attr_name: str, value: Any):
        if not isinstance(value, bool):
            raise ValueError(value)
        self.attr_name = attr_name
        self.value = value

    def __repr__(self):
        if self.value:
            return '(.%s IS EMPTY)' % (self.attr_name, )
        else:
            return '(.%s IS NOT EMPTY)' % (self.attr_name, )


class ContainsFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        from pyrtable.filterutils import airtable_filter_multiple_select_contains
        column_name = self.get_column_name(record_class, self.attr_name)
        return airtable_filter_multiple_select_contains(column_name=column_name, value=self.value)

    def __init__(self, attr_name: str, value: Any):
        self.attr_name = attr_name
        self.value = value

    def __repr__(self):
        return '(.%s CONTAINS %r)' % (self.attr_name, self.value)


class DoesNotContainFilter(BaseFilter):
    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        from pyrtable.filterutils import airtable_filter_multiple_select_does_not_contain
        column_name = self.get_column_name(record_class, self.attr_name)
        return airtable_filter_multiple_select_does_not_contain(column_name=column_name, value=self.value)

    def __init__(self, attr_name: str, value: Any):
        self.attr_name = attr_name
        self.value = value

    def __repr__(self):
        return '(.%s DOES NOT CONTAIN %r)' % (self.attr_name, self.value)


__all__ = ['TrueFilter', 'FalseFilter', 'NotFilter', 'AndFilter', 'OrFilter', 'EqualsFilter', 'NotEqualsFilter',
           'GreaterThanFilter', 'LessThanFilter', 'GreaterThanOrEqualsFilter', 'LessThanOrEqualsFilter',
           'IsEmptyFilter', 'ContainsFilter', 'DoesNotContainFilter']
