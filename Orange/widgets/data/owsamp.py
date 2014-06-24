"""
The SAMP widget allows data to be received or requested through SAMP.
SAMP is the Simple Application Messaging Protocol designed for the
Virtual Observatory.

Please use the SAMP HUB in astropy or an older (<=1.1) JSAMP HUB and
Astro-WISE as client.
"""

import sys
import urllib

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

    catalog_of_interest = "100511"
    """catalog_of_interest specifies the catalog that somehow has been
    set as interesting. Data is pulled from this catalog. For now this
    is hardcoded."""
    # TODO: Use contexts etc. like other widgets do to handle multiple tables
    #   at the same time.
    # TODO: Allow the catalog_of_interest to be set over SAMP in some way.
    # TODO: Perhaps integrate region_of_interest with catalog_of_interest
    #   in some way?

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
        gui.button(self.controlArea, self, "&Pull Rows", callback=self.pull_rows, default=False)

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

        self.samp_client.bind_receive_notification("table.load.votable", self.received_table_load_votable)
        self.samp_client.bind_receive_call("table.load.votable", self.received_table_load_votable_call)
        #self.SAMP_client.bind_receive_call("table.this.is.cool.table", self.table_this_is_cool_table)

        #self.pull_rows()

    def pull_rows(self):
        """
        First experiment for data through SAMP. This is a prototype.
        """
        if self.region_of_interest is None:
            self.region_of_interest = {
               'RA': (1., 359.),
               'DEC': (-89., 89.),
            }

        region_of_interest_in_sql = " AND ".join(
            ''' "%s" BETWEEN %f AND %f ''' % (
                name, values[0], values[1]
            ) for (name, values) in self.region_of_interest.items()
        )

        message = {
            'samp.mtype':'catalog.pull',
            'samp.params':{
                'startsc': str(self.catalog_of_interest),
                'query': urllib.parse.unquote_plus(region_of_interest_in_sql),
                'attributes': [attribute for attribute in self.region_of_interest],
            },
        }
        print("OWSAMP pull_rows", message)
        #        'query': urllib.unquote_plus('ROWNUM <= %i' % (row_index)),
        #        'query': urllib.unquote_plus('"R" < 300'),
        #attributes ['absMag_u', 'absMag_g', 'iC']

        # TODO: Abstract call and properly implement msg_tag.
        self.samp_client.call_all("pull_nr_1", message)


    def received_table_load_votable(self, private_key, sender_id, msg_id, mtype, parameters, extra):
        """
        Read the received VOTable and broadcast.
        """
        print("Call:", private_key, sender_id, msg_id, mtype, parameters, extra)

        # Retrieve and read the VOTable.
        url_table = parameters['url']

        # sys.stdout is redirected by canvas.__main__ via redirect_stdout()
        # in canvas.util.redirect to an
        # Orange.canvas.application.outputview.TextStream object. This
        # has a @queued_blocking flush(), which can result in an "Result not
        # yet ready" RuntimeError from the QueuedCallEvent class.
        # This exception is raised because astropy.io.votable.table uses
        # astropy.utils.xml.iterparser, which uses astropy.utils.data,
        # which uses the Spinner class from astropy.utils.console, which
        # finally uses stdout to output a progress indicator.
        # Orange has its own mechanisms for indicating progress, so it would
        # perhaps be better to try to use that.
        # For now, the Orange redirect of stdout is temporarily disabled
        # while the votable is being parsed.

        stdout_orange = sys.stdout
        sys.stdout = sys.__stdout__
        votable_tree = votable.parse(url_table)
        sys.stdout = stdout_orange

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

    def received_table_load_votable_call(self, private_key, sender_id, msg_id, mtype, parameters, extra):
        """
        Receive a VOTable and reply with success.

        TODO: Only reply with success if there was no problem.
        """
        self.received_table_load_votable(private_key, sender_id, msg_id, mtype, parameters, extra)
        self.samp_client.reply(msg_id, {"samp.status": "samp.ok", "samp.result": {}})

    def disconnect_samp(self):
        """Disconnect from the SAMP HUB"""
        self.samp_client.disconnect()

    def closeEvent(self, ev):
        self.disconnect_samp()
        super().closeEvent(ev)


    def __del__(self):
        """Disconnect from the SAMP Hub on exit."""
        print("OWSAMP __del__")
        self.disconnect_samp()

def main():
    a = QtGui.QApplication(sys.argv)
    ow = OWSAMP()
    ow.show()
    a.exec_()
    ow.saveSettings()

if __name__ == "__main__":
    main()