import os
import unittest
from typing import Optional

from pyrtable.fields import StringField
from pyrtable.record import BaseRecord

api_key: Optional[str]
base_id: Optional[str]
table_id: Optional[str]
has_test_config_data: Optional[bool] = None


def prepare_config_data() -> None:
    global api_key, base_id, table_id, has_test_config_data

    if has_test_config_data is not None:
        return

    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_TEST_BASE_ID')
    table_id = os.getenv('AIRTABLE_TEST_TABLE_ID')
    has_test_config_data = bool(api_key) and bool(base_id) and bool(table_id)


def is_test_config_data_available() -> bool:
    prepare_config_data()
    return has_test_config_data


class TestRecord(BaseRecord):
    class Meta:
        @classmethod
        def get_api_key(cls):
            prepare_config_data()
            return api_key

        @classmethod
        def get_base_id(cls):
            prepare_config_data()
            return base_id

        @classmethod
        def get_table_id(cls):
            prepare_config_data()
            return table_id

    key_field = StringField('Key Field')
    field_1 = StringField('First')
    field_2 = StringField('{Second Field}')
    field_3 = StringField('\'Third" field\\')
    field_4 = StringField('Fourth? Field')
    field_5 = StringField('Fifth! Field')


# noinspection PyMethodMayBeStatic
@unittest.skipUnless(
    is_test_config_data_available(),
    "Server config data and authentication must be provided by AIRTABLE_API_KEY, AIRTABLE_TEST_BASE_ID"
    " and AIRTABLE_TEST_TABLE_ID environment variables")
class ServerTests(unittest.TestCase):
    def test_query(self):
        records = list(TestRecord.objects.all())
        self.assertEqual(len(records), 20)

    def test_filters(self):
        records = list(TestRecord.objects.filter(field_1="Nadin' Trevino"))
        self.assertEqual(len(records), 1)

        records = list(TestRecord.objects.filter(field_2="Sara Bass'"))
        self.assertEqual(len(records), 1)

        records = list(TestRecord.objects.filter(field_3="Jud' Conley"))
        self.assertEqual(len(records), 1)

        records = list(TestRecord.objects.filter(field_4="Rey' Serrano"))
        self.assertEqual(len(records), 1)

        records = list(TestRecord.objects.filter(field_5="Ronnie'n'Murphy"))
        self.assertEqual(len(records), 1)
