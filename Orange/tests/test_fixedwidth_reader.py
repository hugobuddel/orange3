import io
import unittest

import numpy
import os

from Orange.data import ContinuousVariable, DiscreteVariable
from Orange.data.io import TabDelimReader
from Orange.data.io import FixedWidthReader

from Orange.data.fixed_from_tab import  fixed_from_tab

class TestTabReader(unittest.TestCase):
    """
    Go through all the .tab tables available in tests, convert them
    to .fixed tables, read both in and compare them.
    """
    
    names_tables = [
        #'glass', # from datasets
        'housing',
        #'iris', # has spaces in column names, not yet supported
        #'test1', # has spaces in formats, not yet supported
        #'test2', # has spaces in formats and unfinished rows
        'test3',
        'test4',
        'zoo',
    ]
    
    
    def setUp(self):
        for name_table in self.names_tables:
            name_table_tab = name_table + ".tab"
            name_table_fixed = name_table + ".fixed"

            fixed_from_tab(name_table_tab, name_table_fixed)
        
    
    def test_read_easy(self):
        for name_table in self.names_tables:
            #print("Testing {name}.".format(name=name_table))
            name_table_tab = name_table + ".tab"
            name_table_fixed = name_table + ".fixed"
        
            table_tab = TabDelimReader().read_file(name_table_tab)
            table_fixed = FixedWidthReader().read_file(name_table_fixed)
            print(len(table_tab.domain.variables), len(table_fixed.domain.variables))
            
            for var_tab in table_tab.domain.variables:
                var_fixed = [v for v in table_tab.domain.variables if v.name == var_tab.name][0]
                self.assertEqual(var_tab, var_fixed, "Vars not equal! {0}".format(name_table))
            
            for (row_tab, row_fixed) in zip(table_tab, table_fixed):
                for var_tab in table_tab.domain.variables:
                    var_name = var_tab.name
                    self.assertEqual(row_tab[var_name], row_fixed[var_name], "Rows not equal! {0}".format(name_table))

    def test_read_cell(self):
        table_tab = TabDelimReader().read_file('housing.tab')
        tests = [
            ("CRIM", 4),
            ("ZN", 10),
            ("INDUS", 23),
            ("CHAS", 24),
        ]
        for test in tests:
            value_tab = table_tab[test[1]][test[0]]
            value_fixed = FixedWidthReader().read_cell(
                'housing.fixed',
                index_row = test[1],
                name_attribute = test[0],
            )
            self.assertEqual(
                value_tab,
                value_fixed,
                "Value not equal! {test} {value_tab} {value_fixed}".format(
                    test=test,
                    value_tab=value_tab,
                    value_fixed=value_fixed,
                )
            )

    def tearDown(self):
        for name_table in self.names_tables:
            name_table_tab = name_table + ".tab"
            name_table_fixed = name_table + ".fixed"

            os.remove(name_table_fixed)


if __name__ == "__main__":
    unittest.main()
