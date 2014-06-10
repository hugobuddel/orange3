import io
import unittest

import numpy
import os
import shutil

import Orange
from Orange import data
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
        'glass', # from datasets
        'housing',
        'iris', # has spaces in column names, now supported
        #'test1', # has spaces in types, not yet supported
        #'test2', # has spaces in types, and unfinished rows
        #'test3', # has spaces in types
        'test4',
        'zoo',
    ]
    
    
    def setUp(self):
        data.table.dataset_dirs.append("Orange/tests")
        # There must be a better way to get access to the test files
        # than this self.dir_data. However, now it works with 
        # python -m unittest discover Orange/tests

        self.dir_data = Orange.__path__[0] + "/tests/"

        name_table = "glass"
        name_table_tab_org = Orange.__path__[0] + "/datasets/" + name_table + ".tab"
        name_table_tab = self.dir_data + name_table + ".tab"
        shutil.copy(name_table_tab_org, name_table_tab)
        name_table_fixed = self.dir_data + name_table + ".fixed"
        fixed_from_tab(name_table_tab, name_table_fixed)

        for name_table in self.names_tables:
            name_table_tab = self.dir_data + name_table + ".tab"
            name_table_fixed = self.dir_data + name_table + ".fixed"

            fixed_from_tab(name_table_tab, name_table_fixed)


    
    def test_read_easy(self):
        for name_table in self.names_tables:
            #print("Testing {name}.".format(name=name_table))
            name_table_tab = self.dir_data + name_table + ".tab"
            name_table_fixed = self.dir_data + name_table + ".fixed"
        
            table_tab = TabDelimReader().read_file(name_table_tab)
            table_fixed = FixedWidthReader().read_file(name_table_fixed)
            print(len(table_tab.domain.variables), len(table_fixed.domain.variables))
            
            for var_tab in table_tab.domain.variables:
                var_fixed = [v for v in table_fixed.domain.variables if v.name == var_tab.name][0]
                self.assertEqual(var_tab, var_fixed, "Vars not equal! {0}".format(name_table))

            for var_fixed in table_fixed.domain.variables:
                var_tab = [v for v in table_tab.domain.variables if v.name == var_fixed.name][0]
                self.assertEqual(var_tab, var_fixed, "Vars not equal! {0}".format(name_table))

            for (row_tab, row_fixed) in zip(table_tab, table_fixed):
                for var_tab in table_tab.domain.variables:
                    var_name = var_tab.name
                    self.assertEqual(row_tab[var_name], row_fixed[var_name], "Rows not equal! {0}".format(name_table))

    def test_read_cell(self):
        table_tab = TabDelimReader().read_file(self.dir_data + 'housing.tab')
        tests = [
            ("CRIM", 4),
            ("ZN", 10),
            ("INDUS", 23),
            ("CHAS", 24),
        ]
        for test in tests:
            value_tab = table_tab[test[1]][test[0]]
            value_fixed = FixedWidthReader().read_cell(
                self.dir_data + 'housing.fixed',
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
            name_table_fixed = self.dir_data + name_table + ".fixed"
            os.remove(name_table_fixed)

        os.remove(self.dir_data + "glass.tab")

if __name__ == "__main__":
    unittest.main()
