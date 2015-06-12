"""
The InfiniTable is a widget that creates a LazyTable of infinite size!
"""
__author__ = 'buddel'


from Orange.data.lazytable import LazyTable

import os, sys

from PyQt4 import QtGui

from Orange.data import (io, DiscreteVariable, ContinuousVariable)
from Orange.data.domain import Domain


import Orange.widgets.widget

import numpy.random
import hashlib
from collections import OrderedDict

class OWInfiniTable(Orange.widgets.widget.OWWidget):
    """
    The InfiniTable is a widget that creates a LazyTable of infinite size!
    """
    name = "InfiniTable"
    id = "orange.widgets.data.infinitable"
    description = """
    The InfiniTable is a widget that creates a LazyTable of infinite size!
    """
    long_description = """
    The InfiniTable is a widget that creates a LazyTable of infinite size!
    """
    icon = "icons/File.svg"
    author = "Hugo Buddelmeijer"
    maintainer_email = "buddel(@at@)astro.rug.nl"
    priority = 10
    category = "Data"
    keywords = ["data", "read", "lazy"]
    outputs = [{"name": "Data",
                "type": LazyTable,
                "doc": "Generated attribute-valued data set."}]

    # region_of_interest specifies what part of the dataset is interesting
    # according to widgets further in the scheme. See in_region_of_interest()
    # of LazyRowInstance for information about its structure.
    region_of_interest = None

    def __init__(self):
        self.seed = 12345

        # TODO: Where should this row generating function be?
        #  Here, in the LazyTable or in the LazyRowInstance
        self.class_vars = OrderedDict()
        self.class_vars['class'] = lambda row_index: numpy.random.randint(2)

        self.attributes_continuous = OrderedDict()
        # self.attributes_continuous['X'] = lambda row_index: numpy.random.random() * 4.0 + 2.0
        # self.attributes_continuous['Y'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['k'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['l'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['m'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['n'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['o'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['p'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['q'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['r'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['s'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['t'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        # self.attributes_continuous['u'] = lambda row_index: numpy.random.random() * 8.0 + 10.0
        self.attributes_continuous['a'] = lambda row_index: \
            numpy.random.normal(loc=1.0, scale=2.0) \
            if self.pull_cell(row_index, 'class') == 0 else \
            numpy.random.normal(loc=5.0, scale=2.0)
        self.attributes_continuous['b'] = lambda row_index: \
            numpy.random.normal(loc=-3.0, scale=1.0) \
            if self.pull_cell(row_index, 'class') == 0 else \
            numpy.random.normal(loc=1.0, scale=0.5)

        self.data = LazyTable.from_domain(domain = self.pull_domain())
        self.data.widget_origin = self
        self.data.name = "GeneratedTest1"

        # Pull some data so non-lazy aware widgets are not confused.
        self.data.pull_region_of_interest()

        self.send("Data", self.data)



    def pull_header(self):
        # Backward compatibility.
        # TODO: Think of how to implement and use pull_domain() in a general way.
        return self.pull_domain()

    def pull_domain(self):
        """
        Returns the domain of the output data.
        """
        attributes = [
            ContinuousVariable(name=column)
            for column in self.attributes_continuous
        ]
        attributes = [
            ContinuousVariable(name=column)
            for column in self.attributes_continuous
        ]
        # TODO: get values from self.something.
        class_vars = [
            DiscreteVariable(name=column, values=['alpha', 'beta'])
            for column in self.class_vars
        ]
        domain = Domain(
            attributes=attributes,
            class_vars=class_vars,
        )

        return domain

    def pull_length(self):
        """
        Returns the length of the output data.
        """
        # TODO: Change to Infinity later.
        length = 10000000
        # Should work easily.

        #length = 80000000
        # Maximum that seems to work, still fluidly.

        #length = 85000000
        # Doesn't work, hangs Orange.

        #length = numpy.inf
        # Doesn't work because many functions expect and integer for
        # the length of the dataset.

        #numpy.iinfo(numpy.int64).max
        #9223372036854775807
        #length = numpy.iinfo(numpy.int64).max # shows nothing
        # Shows nothing, doesn't hang Orange.

        return length


    def pull_cell(self, index_row, name_attribute):
        """
        Returns a specific value.
        """
        if not isinstance(name_attribute, str):
            name_attribute = name_attribute.name
        # TODO: Use a proper seed that does not repeat itself.
        # TODO: Handle attributes/class_vars/metas properly.
        index_attribute = \
            list(self.class_vars.keys()).index(name_attribute) \
            if name_attribute in self.class_vars \
            else list(self.attributes_continuous.keys()).index(name_attribute)

        seed = \
            self.seed * 10000000000000 + \
            index_row * 100000000 + \
            index_attribute

        state_old = numpy.random.get_state()
        numpy.random.seed(seed)

        if name_attribute in self.class_vars:
            cell = self.class_vars[name_attribute](index_row)
        else:
            cell = self.attributes_continuous[name_attribute](index_row)

        # Reset the state because the attribute generating functions might
        # change the state.
        numpy.random.set_state(state_old)


        return cell

    def pull_region_of_interest(self, number_of_rows=5):
        """
        Pull more rows.

        TODO: Almost verbatim from LazyFile, so perhaps make a base
           LazyWidget class with such functions?
        """
        print("Pulling more data in OWInfiniTable")

        number_of_added_rows = 0
        # Cannot use range(len()) because len will be numpy.inf, therefore
        # use a while loop.
        #for row_index in range(self.data.len_full_data()):
        row_index = -1
        while row_index < self.data.len_full_data()-1:
            row_index += 1
            if not row_index in self.data.row_mapping:
                # self.data[row_index] cannot be used because we want to pass
                # region_of_interest_only=True.
                row = self.data.__getitem__(
                    row_index, region_of_interest_only=True)
                # Only count rows that are in the ROI.
                if row.in_region_of_interest():
                    number_of_added_rows += 1
                    if number_of_added_rows >= number_of_rows:
                        break

        self.send("Data", self.data)

    def set_region_of_interest(self, region_of_interest):
        """
        A region of interest has been indicated, probably by the user.
        Give preference to data in this region when pulling more data.
        """
        self.region_of_interest = region_of_interest

    # TODO: Figure out how to properly stop the data pulling.
    #   closeEvent is also triggered when the info window is closed.
    def closeEvent(self, ev):
        self.data.stop_pulling = True
        super().closeEvent(ev)


    def __del__(self):
        self.data.stop_pulling = True





if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    ow = OWInfiniTable()

    print(ow.pull_header())
    print(ow.pull_cell(100, 'a'))
    print(ow.pull_cell(101, 'a'))
    print(ow.pull_cell(100, 'b'))
    print(ow.pull_cell(100, 'a'))

    ow.data.pull_region_of_interest()
    ow.data.stop_pulling = True

    #ow.show()
    #a.exec_()
    #ow.saveSettings()
