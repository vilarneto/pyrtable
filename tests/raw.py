import unittest

from pyrtable.fields import IntegerField, FloatField, StringField, BooleanField
from pyrtable.filters.raw import *
from pyrtable.filterutils import quote_value
from pyrtable.record import BaseRecord


class TestRecord(BaseRecord):
    int_field = IntegerField('Integer Field')
    float_field = FloatField('Float Field')
    string_field = StringField('String Field')
    boolean_field = BooleanField('Boolean Field')


class RawFilterFormulaTests(unittest.TestCase):
    def test_quote_value(self):
        self.assertEqual(quote_value(0), '0')
        self.assertEqual(quote_value(""), '""')
        self.assertEqual(quote_value(False), 'FALSE()')
        self.assertEqual(quote_value(True), 'TRUE()')

    def test_boolean_filters(self):
        self.assertEqual(TrueFilter().build_formula(TestRecord),
                         "TRUE()")
        self.assertEqual(FalseFilter().build_formula(TestRecord),
                         "FALSE()")

    def test_equals_filter(self):
        self.assertEqual(EqualsFilter('int_field', 15).build_formula(TestRecord),
                         "{Integer Field}=15")
        self.assertEqual(EqualsFilter('float_field', 2.5).build_formula(TestRecord),
                         "{Float Field}=2.5")
        self.assertEqual(EqualsFilter('string_field', "String").build_formula(TestRecord),
                         '{String Field}="String"')
        self.assertEqual(EqualsFilter('boolean_field', True).build_formula(TestRecord),
                         '({Boolean Field})')
        self.assertEqual(EqualsFilter('boolean_field', False).build_formula(TestRecord),
                         'NOT({Boolean Field})')

    def test_not_equals_filter(self):
        self.assertEqual(NotEqualsFilter('int_field', 15).build_formula(TestRecord),
                         "{Integer Field}!=15")
        self.assertEqual(NotEqualsFilter('float_field', 2.5).build_formula(TestRecord),
                         "{Float Field}!=2.5")
        self.assertEqual(NotEqualsFilter('string_field', "String").build_formula(TestRecord),
                         '{String Field}!="String"')

    def test_comparison_filters(self):
        pairs = [
            (GreaterThanFilter, '>'),
            (LessThanFilter, '<'),
            (GreaterThanOrEqualsFilter, '>='),
            (LessThanOrEqualsFilter, '<='),
        ]

        for filter_cls, operator in pairs:
            flt = filter_cls('int_field', 15)
            self.assertEqual(flt.build_formula(TestRecord),
                             "{Integer Field}%s15" % operator)

    def test_and_or_filters(self):
        pairs = [
            (AndFilter, 'AND'),
            (OrFilter, 'OR'),
        ]

        for filter_cls, function in pairs:
            flt = filter_cls(EqualsFilter('int_field', 15))
            self.assertEqual(flt.build_formula(TestRecord),
                             "{Integer Field}=15")

            flt = filter_cls(EqualsFilter('int_field', 15), EqualsFilter('float_field', 2.5))
            self.assertEqual(flt.build_formula(TestRecord), "%s({Integer Field}=15,{Float Field}=2.5)" % function)

            flt = filter_cls(EqualsFilter('int_field', 15), NotEqualsFilter('float_field', 2.5))
            self.assertEqual(flt.build_formula(TestRecord), "%s({Integer Field}=15,{Float Field}!=2.5)" % function)

            flt = filter_cls(EqualsFilter('int_field', 15), NotEqualsFilter('float_field', 2.5),
                             EqualsFilter('string_field', "String"))
            self.assertEqual(flt.build_formula(TestRecord),
                             '%s({Integer Field}=15,{Float Field}!=2.5,{String Field}="String")' % function)

    def test_and_or_with_boolean_filters(self):
        self.assertEqual(OrFilter(TrueFilter()).build_formula(TestRecord),
                         "TRUE()")
        self.assertEqual(AndFilter(FalseFilter()).build_formula(TestRecord),
                         "FALSE()")
        self.assertEqual(OrFilter(TrueFilter(), EqualsFilter('int_field', 15)).build_formula(TestRecord),
                         "TRUE()")
        self.assertEqual(AndFilter(FalseFilter(), EqualsFilter('int_field', 15)).build_formula(TestRecord),
                         "FALSE()")

    def test_not_filter(self):
        flt = EqualsFilter('int_field', 15)
        self.assertEqual(NotFilter(flt).build_formula(TestRecord), "NOT({Integer Field}=15)")
        self.assertEqual(NotFilter(NotFilter(flt)).build_formula(TestRecord), "{Integer Field}=15")
        self.assertEqual(NotFilter(NotFilter(NotFilter(flt))).build_formula(TestRecord), "NOT({Integer Field}=15)")

    def test_not_with_boolean_filters(self):
        self.assertEqual(NotFilter(TrueFilter()).build_formula(TestRecord),
                         "FALSE()")
        self.assertEqual(NotFilter(FalseFilter()).build_formula(TestRecord),
                         "TRUE()")


if __name__ == '__main__':
    unittest.main()
