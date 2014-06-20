"""
The SAMP widget allows data to be received or requested through SAMP.
SAMP is the Simple Application Messaging Protocol designed for the
Virtual Observatory.
"""

import sys

from astropy.vo.samp import SAMPIntegratedClient
from astropy.io import votable

from PyQt4 import QtGui
from Orange.widgets import gui

from Orange.data.lazytable import LazyTable
from Orange.data.table import Table
from Orange.widgets.widget import OWWidget
from Orange.data.variable import ContinuousVariable
from Orange.data.domain import Domain

class OWSAMP(OWWidget):
    """
    The SAMP widget allows data to be received or requested through SAMP.
    SAMP is the Simple Application Messaging Protocol designed for the
    Virtual Observatory.
    """
    name = "SAMP"
    id = "orange.widgets.data.samp"
    description = """
    Creates a SAMP connection and requests or receives data."""
    long_description = """
    Creates a SAMP connection and requests or receives data."""
    icon = "icons/File.svg"
    author = "Hugo Buddelmeijer"
    maintainer_email = "buddel(@at@)astro.rug.nl"
    priority = 10
    category = "Data"
    keywords = ["data", "file", "load", "read", "lazy"]
    outputs = [{"name": "Data",
                "type": LazyTable,
                "doc": "Attribute-valued data set received over SAMP."}]

    # TODO: move this to LazyTable
    stop_pulling = False
    #stop_pulling = True

    region_of_interest = None
    """region_of_interest specifies what part of the data set is interesting
    according to widgets further in the scheme. See in_region_of_interest()
    of LazyRowInstance for information about its structure."""

    def __init__(self):
        super().__init__()

        self.data = None
        """The LazyTable that will be send."""

        # GUI: as simple as possible for now
        box = gui.widgetBox(self.controlArea, "SAMP Info")
        self.infoa = gui.widgetLabel(box, 'SAMP connectivity is running. Would you like to disconnect from the Hub?')
        self.infob = gui.widgetLabel(box, '')
        self.resize(100,50)
        gui.button(self.controlArea, self, "&Disconnect", callback=self.disconnect_samp, default=False)

        # Create a client
        self.samp_client = SAMPIntegratedClient(
            metadata = {
                "samp.name":"Orange Client",
                "samp.description.text":"Orange SAMP connectivity",
                "OrangeClient.version":"0.01"
           }
        )

        # Connect the client
        self.samp_client.connect()

        self.samp_client.bind_receive_call("table.load.votable", self.received_table_load_votable)
        #self.SAMP_client.bind_receive_call("table.this.is.cool.table", self.table_this_is_cool_table)


    def received_table_load_votable(self, private_key, sender_id, msg_id, mtype, parameters, extra):
        print("Call:", private_key, sender_id, msg_id, mtype, parameters, extra)

        # Retrieve and read the VOTable.
        url_table = parameters['url']
        #import time
        #time.sleep(5)
        votable_tree = votable.parse(url_table)
        print("VOTable Tree created")
        votable_table = votable_tree.get_first_table()
        #type(votable)
        #<class 'astropy.io.votable.tree.Table'>
        table = votable_table.to_table()
        #type(table)
        #<class 'astropy.table.table.Table'>
        print("AstroPy table made")

        # Convert the VOTable to a Domain.
        # TODO: Y en metas
        attributes = [
            ContinuousVariable(name=column)
            for column in table.columns
        ]
        domain = Domain(attributes = attributes)
        print("Domain made")

        # Convert the VOTable to a Table
        # Append the Table to LazyTable self.data.
        # (Re)send self.data).
        otable = Table.from_domain(
            domain = domain,
            n_rows = len(table),
        )
        print("Orange Table initialized")
        for i, variable in enumerate(otable.domain.variables):
            otable.X[:,i] = table.columns[variable.name].data

        print("Orange Table filled")
        self.data = otable
        self.send("Data", self.data)
        print("Orange Table send")

    def disconnect_samp(self):
        self.samp_client.disconnect()


def main():
    a = QtGui.QApplication(sys.argv)
    ow = OWSAMP()
    ow.show()
    a.exec_()
    ow.saveSettings()

if __name__ == "__main__":
    main()