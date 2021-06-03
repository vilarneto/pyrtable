import unittest
from typing import Optional

from pyrtable.fields import IntegerField, SingleRecordLinkField
from pyrtable.record import BaseRecord


class TestRecord(BaseRecord):
    class Meta:
        base_id = 'appTestBaseID'
        table_id = 'Test Table ID'

    integer = IntegerField('Integer')


class AnotherTestRecord(BaseRecord):
    class Meta:
        base_id = 'appTestBaseID'
        table_id = 'Another Test Table ID'

    single_link: Optional[TestRecord] = SingleRecordLinkField('Test Field', linked_class=TestRecord)


class NoBaseRecord(BaseRecord):
    class Meta:
        table_id = 'The Table Name'


class NoTableRecord(BaseRecord):
    class Meta:
        base_id = 'appSomething'


class URLTests(unittest.TestCase):
    def test_url(self):
        self.assertEqual(TestRecord.objects.all()
                         .build_url(),
                         'https://api.airtable.com/v0/appTestBaseID/Test%20Table%20ID')
        self.assertEqual(TestRecord.objects.all()
                         .set_base_id('appAnotherID')
                         .build_url(),
                         'https://api.airtable.com/v0/appAnotherID/Test%20Table%20ID')
        self.assertEqual(TestRecord.objects.all()
                         .set_table_id('Another Table ID')
                         .build_url(),
                         'https://api.airtable.com/v0/appTestBaseID/Another%20Table%20ID')
        self.assertEqual(TestRecord.objects.all()
                         .build_url(),
                         'https://api.airtable.com/v0/appTestBaseID/Test%20Table%20ID')
        self.assertEqual(TestRecord.objects.all()
                         .set_base_id('appStrangeID')
                         .set_table_id('Strange table name')
                         .build_url(),
                         'https://api.airtable.com/v0/appStrangeID/Strange%20table%20name')

    def test_url_with_record(self):
        self.assertEqual(TestRecord.objects.all()
                         .build_url(record_id='recSomeID'),
                         'https://api.airtable.com/v0/appTestBaseID/Test%20Table%20ID/recSomeID')
        self.assertEqual(TestRecord.objects.all()
                         .set_base_id('appAnotherID')
                         .build_url(record_id='recSomeID'),
                         'https://api.airtable.com/v0/appAnotherID/Test%20Table%20ID/recSomeID')
        self.assertEqual(TestRecord.objects.all()
                         .set_table_id('Another Table ID')
                         .build_url(record_id='recSomeID'),
                         'https://api.airtable.com/v0/appTestBaseID/Another%20Table%20ID/recSomeID')
        self.assertEqual(TestRecord.objects.all()
                         .build_url(record_id='recSomeID'),
                         'https://api.airtable.com/v0/appTestBaseID/Test%20Table%20ID/recSomeID')
        self.assertEqual(TestRecord.objects.all()
                         .set_base_id('appStrangeID')
                         .set_table_id('Strange table name')
                         .build_url(record_id='recSomeID'),
                         'https://api.airtable.com/v0/appStrangeID/Strange%20table%20name/recSomeID')

    def test_url_incomplete_metadata(self):
        self.assertRaises(ValueError,
                          NoBaseRecord.objects.all()
                          .build_url)
        self.assertRaises(ValueError,
                          NoBaseRecord.objects.all()
                          .set_table_id('Something')
                          .build_url)
        self.assertEqual(NoBaseRecord.objects.all()
                         .set_base_id('appAnotherID')
                         .build_url(),
                         'https://api.airtable.com/v0/appAnotherID/The%20Table%20Name')
        self.assertEqual(NoBaseRecord.objects.all()
                         .set_base_id('appAnotherID')
                         .set_table_id('Something')
                         .build_url(),
                         'https://api.airtable.com/v0/appAnotherID/Something')

        self.assertRaises(ValueError,
                          NoTableRecord.objects.all()
                          .build_url)
        self.assertRaises(ValueError,
                          NoTableRecord.objects.all()
                          .set_base_id('appSomeValue')
                          .build_url)
        self.assertEqual(NoTableRecord.objects.all()
                         .set_table_id('Something')
                         .build_url(),
                         'https://api.airtable.com/v0/appSomething/Something')
        self.assertEqual(NoTableRecord.objects.all()
                         .set_base_id('appSomeValue')
                         .set_table_id('Something')
                         .build_url(),
                         'https://api.airtable.com/v0/appSomeValue/Something')

    def test_linked_urls(self):
        # To avoid server hits / API key fetching we'll “fake” cached records

        from pyrtable.context import set_default_context, SimpleCachingContext

        # Set up the caching mechanism

        caching_context = SimpleCachingContext()
        set_default_context(caching_context)

        # Cache some values

        record = TestRecord(_base_id=TestRecord.Meta.base_id, _table_id=TestRecord.Meta.table_id)
        record.consume_airtable_data({
            'id': 'rec1',
            'createdTime': '2020-01-02T03:04:05.678Z',
            'fields': {
                'Integer': 1,
            },
        })
        caching_context.pre_cache(record)

        record = TestRecord(_base_id='appChanged', _table_id=TestRecord.Meta.table_id)
        record.consume_airtable_data({
            'id': 'rec2',
            'createdTime': '2020-01-02T03:04:05.678Z',
            'fields': {
                'Integer': 2,
            },
        })
        caching_context.pre_cache(record)

        # Now to the actual tests

        record = AnotherTestRecord(_base_id=AnotherTestRecord.Meta.base_id, _table_id=AnotherTestRecord.Meta.table_id)
        record.consume_airtable_data({
            'id': 'recTR',
            'createdTime': '2020-01-02T03:04:05.678Z',
            'fields': {
                'Test Field': ['rec1'],
            },
        })
        self.assertEqual(record.single_link.integer, 1)

        record = AnotherTestRecord(_base_id='appChanged', _table_id=AnotherTestRecord.Meta.table_id)
        record.consume_airtable_data({
            'id': 'recTR',
            'createdTime': '2020-01-02T03:04:05.678Z',
            'fields': {
                'Test Field': ['rec1'],
            },
        })
        # Break because it needs the API key (since it's not cached -- 'rec1' refers to another base)
        self.assertRaises(KeyError, lambda: record.single_link)

        record = AnotherTestRecord(_base_id=AnotherTestRecord.Meta.base_id, _table_id=AnotherTestRecord.Meta.table_id)
        record.consume_airtable_data({
            'id': 'recTR',
            'createdTime': '2020-01-02T03:04:05.678Z',
            'fields': {
                'Test Field': ['rec2'],
            },
        })
        # Break because it needs the API key (since it's not cached)
        self.assertRaises(KeyError, lambda: record.single_link)

        record = AnotherTestRecord(_base_id='appChanged', _table_id=AnotherTestRecord.Meta.table_id)
        record.consume_airtable_data({
            'id': 'recTR',
            'createdTime': '2020-01-02T03:04:05.678Z',
            'fields': {
                'Test Field': ['rec2'],
            },
        })
        self.assertEqual(record.single_link.integer, 2)
