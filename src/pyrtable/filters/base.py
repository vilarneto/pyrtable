from typing import Type, TYPE_CHECKING


if TYPE_CHECKING:
    from pyrtable.fields import BaseField
    from pyrtable.record import BaseRecord


class BaseFilter:
    @staticmethod
    def get_field_object(record_class: Type['BaseRecord'], attr_name: str) -> 'BaseField':
        try:
            return next(field for field_attr_name, field in record_class.iter_fields()
                        if field_attr_name == attr_name)
        except StopIteration:
            raise AttributeError("%r has no attribute %r" % (record_class, attr_name))

    @staticmethod
    def get_column_name(record_class: Type['BaseRecord'], attr_name: str) -> str:
        return BaseFilter.get_field_object(record_class=record_class, attr_name=attr_name).column_name

    def __and__(self, other):
        from .raw import AndFilter

        if not isinstance(other, BaseFilter):
            return NotImplemented

        return AndFilter(self, other)

    def __or__(self, other):
        from .raw import OrFilter

        if not isinstance(other, BaseFilter):
            return NotImplemented

        return OrFilter(self, other)

    def __invert__(self):
        from .raw import NotFilter

        if isinstance(self, NotFilter):
            return self.filter
        return NotFilter(self)

    def build_formula(self, record_class: Type['BaseRecord']) -> str:
        raise NotImplementedError()


__all__ = ['BaseFilter']
