
from Orange.data.lazytable import LazyTable

import os, sys
from PyQt4 import QtCore
from PyQt4 import QtGui
from Orange.widgets import widget, gui
from Orange.widgets.settings import Setting
from Orange.data.table import Table, get_sample_datasets_dir
from Orange.data import StringVariable, DiscreteVariable, ContinuousVariable

from Orange.data import (domain as orange_domain,
                         io, DiscreteVariable, ContinuousVariable)

"""
The LazyFile widget is a lazy version of the original File widget.
"""

# Importing the OWFile directly is not possible, because this will
# register the OWLazyFile as the normal File widget due to the
# metaclass.
#from Orange.widgets.data.owfile import OWFile
import Orange.widgets.data.owfile


class OWLazyFile(Orange.widgets.data.owfile.OWFile):
    """
    The OWLazyFile widget sends a LazyTable as output. This lazy table
    initially contains no instatiated data. The LazyTable will defer
    any requests for data that it doesn't yet hold to the widget that
    created it. The OWLazyFile widget can read only fixed width column
    files, because this allows the widget to read only the parts of
    the table that are actually needed.
    """
    name = "LazyFile"
    id = "orange.widgets.data.lazyfile"
    description = """
    Opens a fixed width column file, reads out the features and the
    number of instances but not the data itself. Sends a LazyTable
    as output."""
    long_description = """
    The common start of a schema, which reads the data from a file. The widget
    maintains a history of most recently used data files. For convenience, the
    history also includes a directory with the sample data sets that come with
    Orange."""
    icon = "icons/File.svg"
    author = "Hugo Buddelmeijer"
    maintainer_email = "buddel(@at@)astro.rug.nl"
    priority = 10
    category = "Data"
    keywords = ["data", "file", "load", "read","lazy"]
    outputs = [{"name": "Data",
                "type": LazyTable,
                "doc": "Attribute-valued data set read from the input file."}]

    formats = {".fixed": "Fixed-width file"}
    
    loaded_file = None
    
    def pull_header(self):
        """
        Returns the domain of the output data.
        """
        domain = io.FixedWidthReader().read_header(self.loaded_file)
        return domain
    
    def pull_length(self):
        """
        Returns the length of the output data.
        """
        length = io.FixedWidthReader().count_lines(self.loaded_file)
        return length
    
    #def pull_row(self, index_row):
    #    data = io.FixedWidthReader().read_file(self.loaded_file)
    #    return data[index_row-1]
    
    def pull_cell(self, index_row, name_attribute):
        """
        Returns a specific value.
        """
        if not isinstance(name_attribute, str):
            name_attribute = name_attribute.name
        #print("Pulling cell {} {} {}".format(self.loaded_file, index_row, name_attribute))
        cell = io.FixedWidthReader().read_cell(
            self.loaded_file,
            index_row,
            name_attribute
        )
        return cell

    # Open a file, create data from it and send it over the data channel
    def open_file(self, fn, preload_rows = 'auto'):
        self.error()
        self.warning()
        self.information()

        if not os.path.exists(fn):
            dirname, basename = os.path.split(fn)
            if os.path.exists(os.path.join(".", basename)):
                fn = os.path.join(".", basename)
                self.information("Loading '{}' from the current directory."
                                 .format(basename))
        if fn == "(none)":
            self.send("Data", None)
            self.infoa.setText("No data loaded")
            self.infob.setText("")
            self.warnings.setText("")
            return

        
        self.loaded_file = fn

        domain = self.pull_header()
        
        self.infoa.setText(
            '{} instance(s), {} feature(s), {} meta attributes'
            .format(self.pull_length(), len(domain.attributes), len(domain.metas)))
        if isinstance(domain.class_var, ContinuousVariable):
            self.infob.setText('Regression; Numerical class.')
        elif isinstance(domain.class_var, DiscreteVariable):
            self.infob.setText('Classification; Discrete class with {} values.'
                               .format(len(domain.class_var.values)))
        elif data.domain.class_vars:
            self.infob.setText('Multi-target; {} target variables.'
                               .format(len(data.domain.class_vars)))
        else:
            self.infob.setText("Data has no target variable.")

        # What does this do?
        #addOrigin(data, fn)
        
        # make new data and send it
        #data = LazyTable()
        #data.domain = domain
        # Creating the LazyTable from the domain will ensure that
        # X, Y and metas are set as well, to empty numpy arrays.
        data = LazyTable.from_domain(domain)


        data.widget_origin = self

        # The name is necessary for the scatterplot
        fName = os.path.split(fn)[1]
        if "." in fName:
            data.name = fName[:fName.rfind('.')]
        else:
            data.name = fName

        # What does this do?
        #self.dataReport = self.prepareDataReport(data)

        self.data = data

        # Ensure that some data is always available.
        # TODO: More proper support for this, e.g. by allowing slow
        #   growth of the table over time.
        #nr_of_rows_to_add = min(5, len(data))

        if isinstance(preload_rows, int):
            nr_of_rows_to_add = preload_rows
        elif preload_rows == 'auto':
            nr_of_rows_to_add = min(5, data.len_full_data())
        else:
            nr_of_rows_to_add = 0

        for row_index in range(nr_of_rows_to_add):
            row = self.data[row_index]

        self.send("Data", data)

    


if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    ow = OWLazyFile()
    ow.show()
    a.exec_()
    ow.saveSettings()
