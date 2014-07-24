from PyQt4.QtGui import QApplication

import unittest

import numpy
import os
import shutil

import Orange
from Orange import data
from Orange.data import ContinuousVariable, DiscreteVariable
from Orange.widgets.data.infinitable import OWInfiniTable

import Orange.data.filter as data_filter

class LazyFilter(unittest.TestCase):
    """
    Test whether the Filter classes can return LazyTables.
    """

    @classmethod
    def setUpClass(cls):
        cls.qApp = QApplication([])

    @classmethod
    def tearDownClass(cls):
        cls.qApp.quit()



if __name__ == "__main__":
    # TODO: Make a real test out of this!

    #unittest.main()

    qApp = QApplication([])
    widget_infinitable = OWInfiniTable()

    # No automatic pulling
    widget_infinitable.data.stop_pulling = True

    data1 = widget_infinitable.data

    #print(widget_infinitable.data.X.shape)
    #print(widget_infinitable.data[10]['X'])
    # 3.941
    #print(widget_infinitable.data[11]['X'])
    # 2.025

    for (i, row) in enumerate(data1):
        print(i, row['X'])
        if i > 10:
            break


    domain = widget_infinitable.data.domain
    filters = data_filter.Values()
    attr_name = 'X'
    oper = data_filter.FilterContinuous.Less
    values = ('3', )

    attr_index = domain.index(attr_name)
    attr = domain[attr_index]
    filter = data_filter.FilterContinuous(
        attr_index, oper, *[float(v) for v in values]
    )

    filters.conditions.append(filter)

    data2 = filters(widget_infinitable.data)
    for (i, row) in enumerate(data2):
        print(i, row['X'])
        if i > 10:
            break

    #print(matching_output.__class__)
    # <class 'Orange.data.table.Table'>

    #print(matching_output.X.shape)

