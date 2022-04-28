import unittest

from pyrtable.fields import FloatField, IntegerField, MultipleSelectionField, StringField
from pyrtable.filters import Q
from pyrtable.record import BaseRecord


class TestRecord(BaseRecord):
    int_field = IntegerField('Integer Field')
    float_field = FloatField('Float Field')
    string_field = StringField('String Field')
    multi_sel_field = MultipleSelectionField('MultiSel Field')


class QTests(unittest.TestCase):
    def test_equals_filter(self):
        self.assertEqual(Q(int_field=15).build_formula(TestRecord),
                         "{Integer Field}=15")
        self.assertEqual(Q(float_field=2.5).build_formula(TestRecord),
                         "{Float Field}=2.5")
        self.assertEqual(Q(string_field="String").build_formula(TestRecord),
                         '{String Field}="String"')

    def test_not_equals_filter(self):
        self.assertEqual(Q(int_field__ne=15).build_formula(TestRecord),
                         "{Integer Field}!=15")
        self.assertEqual(Q(float_field__ne=2.5).build_formula(TestRecord),
                         "{Float Field}!=2.5")
        self.assertEqual(Q(string_field__ne="String").build_formula(TestRecord),
                         '{String Field}!="String"')

    def test_comparison_filters(self):
        pairs = [
            ('gt', '>'),
            ('lt', '<'),
            ('gte', '>='),
            ('lte', '<='),
            ('ge', '>='),
            ('le', '<='),
        ]

        for filter_cls, operator in pairs:
            flt = Q(**{'int_field__%s' % filter_cls: 15})
            self.assertEqual(flt.build_formula(TestRecord),
                             "{Integer Field}%s15" % operator)

    def test_multiple_selection_filters(self):
        self.assertEqual(Q(multi_sel_field__contains='Value').build_formula(TestRecord),
                         'FIND(", "&"Value"&", ",", "&{MultiSel Field}&", ")>0')
        self.assertEqual(Q(multi_sel_field__excludes='Value').build_formula(TestRecord),
                         'FIND(", "&"Value"&", ",", "&{MultiSel Field}&", ")=0')

    def test_and_filter(self):
        flt = Q(int_field=15) & Q(float_field=2.5)
        self.assertEqual(flt.build_formula(TestRecord),
                         "AND({Integer Field}=15,{Float Field}=2.5)")

        flt = Q(int_field=15) & Q(float_field__ne=2.5)
        self.assertEqual(flt.build_formula(TestRecord),
                         "AND({Integer Field}=15,{Float Field}!=2.5)")

        flt = Q(int_field=15) & Q(float_field__ne=2.5) & Q(string_field="String")
        self.assertEqual(flt.build_formula(TestRecord),
                         'AND({Integer Field}=15,{Float Field}!=2.5,{String Field}="String")')

        flt = Q(int_field=15) & (Q(float_field__ne=2.5) & Q(string_field="String"))
        self.assertEqual(flt.build_formula(TestRecord),
                         'AND({Integer Field}=15,{Float Field}!=2.5,{String Field}="String")')

        flt = (Q(int_field__ne=1) & Q(int_field__ne=2)) & (Q(int_field__ne=3) & Q(int_field__ne=4))
        self.assertEqual(flt.build_formula(TestRecord),
                         'AND({Integer Field}!=1,{Integer Field}!=2,{Integer Field}!=3,{Integer Field}!=4)')

    def test_or_filter(self):
        flt = Q(int_field=15) | Q(float_field=2.5)
        self.assertEqual(flt.build_formula(TestRecord),
                         "OR({Integer Field}=15,{Float Field}=2.5)")

        flt = Q(int_field=15) | Q(float_field__ne=2.5)
        self.assertEqual(flt.build_formula(TestRecord),
                         "OR({Integer Field}=15,{Float Field}!=2.5)")

        flt = Q(int_field=15) | Q(float_field__ne=2.5) | Q(string_field="String")
        self.assertEqual(flt.build_formula(TestRecord),
                         'OR({Integer Field}=15,{Float Field}!=2.5,{String Field}="String")')

        flt = Q(int_field=15) | (Q(float_field__ne=2.5) | Q(string_field="String"))
        self.assertEqual(flt.build_formula(TestRecord),
                         'OR({Integer Field}=15,{Float Field}!=2.5,{String Field}="String")')

        flt = (Q(int_field=1) | Q(int_field=2)) | (Q(int_field=3) | Q(int_field=4))
        self.assertEqual(flt.build_formula(TestRecord),
                         'OR({Integer Field}=1,{Integer Field}=2,{Integer Field}=3,{Integer Field}=4)')

    def test_not_filter(self):
        flt = Q(int_field=15)
        self.assertEqual((~flt).build_formula(TestRecord), "NOT({Integer Field}=15)")
        self.assertEqual((~(~flt)).build_formula(TestRecord), "{Integer Field}=15")
        self.assertEqual((~(~(~flt))).build_formula(TestRecord), "NOT({Integer Field}=15)")


if __name__ == '__main__':
    unittest.main()
