from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Tuple, Type, Union

from .base import BaseField
from .valueset import ValueSet, validator_from_enum

if TYPE_CHECKING:
    from pyrtable._baseandtable import BaseAndTableProtocol


class _AbstractSelectionField(BaseField, ABC):
    _enum_class: Optional[Type[Enum]] = None

    def __init__(self, column_name: str, choices: Optional[Union[Type[Enum], List[Tuple[Any, Any]]]] = None, **kwargs):
        if choices is not None:
            import inspect

            if inspect.isclass(choices) and issubclass(choices, Enum):
                self._enum_class = choices

                choices = list((value, value.value) for value in choices)

            self._raw_to_value = {b: a for a, b in choices}
            self._value_to_raw = {a: b for a, b in choices}

        else:
            self._raw_to_value = {}
            self._value_to_raw = {}

        super().__init__(column_name, **kwargs)


class SingleSelectionField(_AbstractSelectionField):
    def decode_from_airtable(self, value: Optional[str], base_and_table: 'BaseAndTableProtocol') -> Optional[Any]:
        return self._raw_to_value.get(value, value)

    def encode_to_airtable(self, value: Optional[Any]) -> Optional[str]:
        return self._value_to_raw.get(value, value)


class MultipleSelectionField(_AbstractSelectionField):
    def _create_value_set(self):
        if self._enum_class is not None:
            validator = validator_from_enum(self._enum_class)
        else:
            validator = None
        return ValueSet(validator=validator)

    def clone_value(self, value: ValueSet) -> ValueSet:
        return ValueSet(value)

    def decode_from_airtable(self, value: Optional[List[str]], base_and_table: 'BaseAndTableProtocol') -> ValueSet:
        if value is not None:
            value = [self._raw_to_value.get(item, item) for item in value]
        return self.validate(value, base_and_table=base_and_table)

    def encode_to_airtable(self, value: Optional[ValueSet]) -> Optional[List[str]]:
        if not value:
            return None
        return [self._value_to_raw.get(item, item) for item in value]

    def validate(self, value: Optional[Iterable[Any]], base_and_table: 'BaseAndTableProtocol') -> ValueSet:
        value_set = self._create_value_set()
        if value is not None:
            value_set.set(value)
        return value_set


__all__ = ['SingleSelectionField', 'MultipleSelectionField']
