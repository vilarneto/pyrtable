from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Any, Callable, Type


if TYPE_CHECKING:
    from pyrtable._baseandtable import _BaseAndTableProtocol
    from pyrtable.record import BaseRecord


class BaseField:
    attr_name: Optional[str] = None
    default_value: Optional[Any] = None
    normalize: Optional[Callable[[Any], Any]] = None
    normalize_from_attr_name: Optional[str] = None
    skip_normalization_if_filled: bool
    _record: Optional[BaseRecord]

    @classmethod
    def _install_extra_properties(cls, record_cls: Type['BaseRecord'], attr_name: str):
        pass

    def __init__(self, column_name: str, default=None, read_only: Optional[bool] = None,
                 normalize=None, normalize_from=None,
                 skip_normalization_if_filled=False):
        if read_only and default is not None:
            raise ValueError('Cannot set a default value for a read-only field')

        self._column_name = column_name
        self._read_only = read_only
        self.default_value = default
        self.normalize = normalize
        self.normalize_from_attr_name = normalize_from
        self.skip_normalization_if_filled = skip_normalization_if_filled

    @property
    def column_name(self) -> Optional[str]:
        return self._column_name

    @property
    def read_only(self):
        if self._read_only is not None:
            return self._read_only
        # noinspection PyProtectedMember
        record_read_only = self._record._get_meta_attr('read_only', None)
        if record_read_only is not None:
            return record_read_only
        return False

    def __get__(self, instance: BaseRecord, owner):
        # noinspection PyProtectedMember
        return instance._fields_values.get(self.attr_name)

    def __set__(self, instance: BaseRecord, value):
        if self.read_only and self._record.id is not None:
            raise AttributeError('%s: This field is read-only' % self.attr_name)
        # noinspection PyProtectedMember
        instance._fields_values[self.attr_name] = self.validate(value, base_and_table=instance)

    @classmethod
    def is_same_value(cls, lhs, rhs) -> bool:
        return lhs == rhs

    def validate(self, value: Any, base_and_table: '_BaseAndTableProtocol') -> Any:
        """Validate the value before storing it.

        Validation means changing the value to appropriate form (e.g., making sure it's converted to a specific class or
        stripping spaces) and/or raising an exception if the value cannot be accepted.

        :param value: The value that's being stored.
        :param base_and_table: The base-and-table info holder (usually the record itself)
        :return: The accepted value for storage.
        :raise: `ValueError` if the value value cannot be accepted.
        """
        return value

    def decode_from_airtable(self, value, base_and_table: '_BaseAndTableProtocol'):
        """
        Decode a field value retrieved through Airtable JSON API into the corresponding Python value.

        :param value: The field value retrieved from the server.
        :param base_and_table: The base-and-table info holder (usually the record itself)
        :return: The corresponding Python value.
        """
        raise NotImplementedError()

    def encode_to_airtable(self, value):
        """
        Encode a native Python value into a field value ready to send to Airtable JSON API.

        :param value: The Python value.
        :return: The corresponding field value ready to send to the server.
        """
        raise NotImplementedError()

    def clone_value(self, value: Any) -> Any:
        """
        Clone (create an independent copy of) a value so it can be compared later for changes.

        :param value: Value to be cloned.
        :return: Cloned value.
        """
        return value

    def __repr__(self):
        if self.attr_name is None:
            attr_name = '(unbound field)'
        else:
            attr_name = self.attr_name

        return '<%s: %s>' % (self.__class__.__name__, attr_name)
