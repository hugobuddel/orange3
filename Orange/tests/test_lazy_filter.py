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
        print(i, row['a'])
        if i > 10:
            break


    domain = widget_infinitable.data.domain

    attr_name = 'a'
    oper = data_filter.FilterContinuous.Less
    values = ('3', )

    attr_index = domain.index(attr_name)
    attr = domain[attr_index]
    myfilter = data_filter.FilterContinuous(
        attr_index, oper, *[float(v) for v in values]
    )

    #filters = data_filter.Values()
    #filters.conditions.append(filter)
    conditions_out = [myfilter]
    filters = data_filter.Values(conditions_out)

    data2 = filters(widget_infinitable.data)
    for (i, row) in enumerate(data2):
        print(i, row['a'])
        if i > 10:
            break
    
    print(len(data2))
    print(data2[123]['a'])
    print(len(data2))

    matching_output = data1._filter_values(filters)
    len(matching_output)
    0
    matching_output.__class__
    #<class 'Orange.data.lazytable.LazyTable'>
    matching_output[2]       
    # [0.863, -1.443 | alpha]
    len(matching_output)
    1

