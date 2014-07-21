"""
The OWLazyWidget is the base class for the LazyWidgets.
"""

import Orange.widgets.widget


# TODO: Perhaps later add Lazy widgets that 'send' other data?
#
#class OWLazyWidget(Orange.widgets.widget.OWWidget):
#    """
#    The OWLazyWidget is a base class for all LazyWidgets.
#    Currently, it is only a base class for widgets that 'send' a LazyTable.
#    """
#    ...
#
#class OWLazyTableWidget(OWLazyWidget):

class OWLazyTableWidget(Orange.widgets.widget.OWWidget):
    """
    The OWLazyTableWidget is a base class for all LazyWidgets that 'send'
    a LazyTable.
    """

    # TODO: Follow PEP 3119 "Introducing Abstract Base Classes"
    #   http://legacy.python.org/dev/peps/pep-3119/

    def __init__(self):
        super().__init__()

        self.data = None
        """The LazyTable that will be send."""
        # TODO: Rename this to self.data_out to prevent confusion with
        #   incoming data, which is usually called self.data.
        #   https://github.com/hugobuddel/orange3/issues/6
        # TODO: Add functionality to create an empty LazyTable here?
        #   E.g. with the proper domain and such.
        # TODO: Implement context and such so it's possible to have multiple
        #   output (and input?) tables for the same widget.



    ######
    # Pull specific parts of the data.
    #

    def pull_domain(self):
        raise NotImplementedError

    def pull_length(self):
        raise NotImplementedError

    def pull_cell(self, index_row, name_attribute):
        raise NotImplementedError



    #####
    # Pull Region of interest.
    #

    def set_region_of_interest(self, region_of_interest):
        # TODO: Something sensible, like
        #self.region_of_interest = region_of_interest
        raise NotImplementedError

    def pull_region_of_interest(self, number_of_rows=5):
        # TODO: Don't really on number_of_rows
        raise NotImplementedError


    #####
    # Stop pulling.
    #

    # TODO: Figure out how to properly stop the data pulling.
    #   closeEvent is also triggered when the info window is closed.
    def closeEvent(self, ev):
        self.data.stop_pulling = True
        super().closeEvent(ev)


    def __del__(self):
        self.data.stop_pulling = True


