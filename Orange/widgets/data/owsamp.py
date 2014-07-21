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
import Orange.widgets.lazywidget
from Orange.data.variable import ContinuousVariable
from Orange.data.domain import Domain

class OWSAMP(Orange.widgets.lazywidget.OWLazyTableWidget):
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

    # catalog_of_interest = "100511" # still to complex
    #_catalog_of_interest = "892271" # based on KiDS DR2
    #_catalog_of_interest = "898581" # SA based on 892271
    #_catalog_of_interest = "898771" # SLW based on SA above
    _catalog_of_interest = "" # Can now be set through SAMP.


    """catalog_of_interest specifies the catalog that somehow has been
    set as interesting. Data is pulled from this catalog. For now this
    is hardcoded."""
    # TODO: Store the catalog_of_interest as a setting.
    # TODO: Use contexts etc. like other widgets do to handle multiple tables
    #   at the same time.
    # TODO: Allow the catalog_of_interest to be set over SAMP in some way.
    # TODO: Perhaps integrate region_of_interest with catalog_of_interest
    #   in some way?

    @property
    def catalog_of_interest(self):
        print("CoI getter")
        return self._catalog_of_interest

    @catalog_of_interest.setter
    def catalog_of_interest(self, value):
        print("CoI setter, %s" % (value))
        self._catalog_of_interest = value
        self.we_have_a_new_table()

    def we_have_a_new_table(self):
        # TODO: think of better name for this function.
        domain = self.pull_domain()
        self.old_region_of_interest = None
        #self.region_of_interest = None
        data = LazyTable.from_domain(domain=domain)
        data.widget_origin = self
        self.data = data
        self.send("Data", self.data)
        print("Orange Table send")

    def pull_length(self):
        # TODO: implement
        #length = 0
        length = self.data.X.shape[0] if self.data is not None else 0
        return length

    def __init__(self):
        super().__init__()

        self.data = None
        """The LazyTable that will be send."""

        # GUI: as simple as possible for now
        box = gui.widgetBox(self.controlArea, "SAMP Info")
        self.infoa = gui.widgetLabel(widget=box, label='SAMP status unknown.')

        box_input_catalog = gui.widgetBox(box, orientation=0)
        self.input_catalog_text = gui.widgetLabel(widget=box_input_catalog , label='Catalog')
        self.input_catalog = gui.lineEdit(widget=box_input_catalog , master=self, value='catalog_of_interest')

        #self.resize(100,50)
        self.button_disconnect = gui.button(self.controlArea, self, "&Disconnect", callback=self.disconnect_samp, default=False)
        self.button_connect = gui.button(self.controlArea, self, "&Connect", callback=self.connect_samp, default=False)
        self.button_disconnect.setHidden(True)
        #gui.button(self.controlArea, self, "&Pull Rows", callback=self.pull_rows, default=False)
        gui.button(self.controlArea, self, "&Set Table", callback=self.we_have_a_new_table, default=False)

        # Create a SAMP client and connect to HUB.
        # Do not make the client in __init__ because this does not allow
        # the client to disconnect and reconnect again.
        self.samp_client = None
        self.connect_samp()

        #self.pull_rows()

    def pull_region_of_interest(self):
        if self.region_of_interest is None:
            self.region_of_interest = {
               #'RA': (1., 359.),
               #'DEC': (-89., 89.),
            }

        if self.old_region_of_interest == self.region_of_interest:
            # We are already getting this data. With SAMP we don't have to
            # keep requesting.
            # TODO: make SAMP widget only keep sending data upon request
            pass
        else:
            self.old_region_of_interest = self.region_of_interest
            print("Pulling ROI",self.region_of_interest)
            self.pull_rows()


    def pull_rows(self):
        """
        First experiment for data through SAMP. This is a prototype.
        """
        if self.data is None:
            self.we_have_a_new_table()

        extra_attributes = ['A', 'B', 'SLID', 'SID', 'HTM']

        region_of_interest_in_sql = " AND ".join(
            ''' "%s" BETWEEN %f AND %f ''' % (
                name, values[0], values[1]
            ) for (name, values) in self.region_of_interest.items()
        ) if len(self.region_of_interest) else ""

        # TODO: Make it possible to specify attributes.
        #   However, this might require significant changes in the way the
        #   data is stored in the LazyTable.
        message = {
            'samp.mtype':'catalog.pull',
            'samp.params':{
                'startsc': str(self.catalog_of_interest),
                'query': urllib.parse.unquote_plus(region_of_interest_in_sql),
                #'attributes': [attribute for attribute in self.region_of_interest],
                #'attributes': [attribute for attribute in self.region_of_interest] + extra_attributes,
                'attributes': [attribute.name for attribute in self.data.domain],
            },
        }
        print("OWSAMP pull_rows", message['samp.params']['startsc'], message['samp.params']['query'])
        #        'query': urllib.unquote_plus('ROWNUM <= %i' % (row_index)),
        #        'query': urllib.unquote_plus('"R" < 300'),
        #attributes ['absMag_u', 'absMag_g', 'iC']

        # TODO: Abstract call and properly implement msg_tag.
        self.samp_client.call_all("pull_nr_1", message)

    def pull_domain(self):
        """
        Requests information about the table over SAMP.
        """
        message = {
            'samp.mtype':'target.object.info',
            'samp.params':{
                'class': 'SourceCollection',
                'id': self.catalog_of_interest,
            },
        }

        # TODO: not use call_and_wait, just call
        id_awe = list(self.samp_client.get_subscribed_clients(mtype="target.object.info"))[0]
        reply = self.samp_client.call_and_wait(message=message, timeout="20", recipient_id = id_awe)

        columns = [a['value'] for a in reply['samp.result']['properties'] if a['name'][:10] == 'attribute|']

        # Create a Domain.
        # TODO: Y en metas, but we don't have this information!
        attributes = [
            ContinuousVariable(name=column)
            for column in columns
        ]
        domain = Domain(attributes = attributes)
        print("Domain made")

        return domain





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
        # TODO: Use from_domain() implicitly from __init__().
        # TODO: Include support to stop_pulling immediately.
        #otable = Table.from_domain(
        otable = LazyTable.from_domain(
        #otable = LazyTable(
            domain = domain,
            n_rows = len(table),
        #    stop_pulling = True,
        )
        otable.stop_pulling = True
        # TODO: set widget_origin?
        print("Orange Table initialized")
        for i, variable in enumerate(otable.domain.variables):
            otable.X[:,i] = table.columns[variable.name].data

        print("Orange Table filled")
        if self.data is None:
            self.data = otable
        else:
            self.data.extend(otable)
            # TODO: Why doesn't this work?:
            #for row in otable:
            #    self.data.append(row)


        self.send("Data", self.data)
        print("Orange Table send")

    # TODO: Implement the messages_received_cache in a nicer way.
    messages_received_cache = []
    def received_table_load_votable_call(self, private_key, sender_id, msg_id, mtype, parameters, extra):
        """
        Receive a VOTable and reply with success.

        TODO: Only reply with success if there was no problem.
        """
        if msg_id in self.messages_received_cache:
            print("Message repeated!", msg_id)
            #self.samp_client.reply(msg_id, {"samp.status": "samp.ok", "samp.result": {}})
            return

        self.messages_received_cache.append(msg_id)
        print("Call:", private_key, sender_id, msg_id, mtype, parameters, extra)
        self.samp_client.reply(msg_id, {"samp.status": "samp.ok", "samp.result": {}})
        print("Reply Send")
        self.received_table_load_votable(private_key, sender_id, msg_id, mtype, parameters, extra)
        print("Table loaded")

    def received_target_object_highlight_call(self, private_key, sender_id, msg_id, mtype, parameters, extra):
        if msg_id in self.messages_received_cache:
            print("Message repeated!", msg_id)
            #self.samp_client.reply(msg_id, {"samp.status": "samp.ok", "samp.result": {}})
            return

        self.messages_received_cache.append(msg_id)
        print("Call:", private_key, sender_id, msg_id, mtype, parameters, extra)
        self.samp_client.reply(msg_id, {"samp.status": "samp.ok", "samp.result": {}})
        print("Reply Send")
        self.catalog_of_interest = parameters['id']
        print("Table loaded")


    def disconnect_samp(self):
        """Disconnect from the SAMP HUB"""
        self.samp_client.disconnect()

        self.infoa.setText("SAMP disconnected.")
        self.button_disconnect.setHidden(True)
        self.button_connect.setHidden(False)

    def connect_samp(self):
        # Create a client. This has to be done on connect, because a
        # disconnected client cannot be reconnected.
        # TODO: Proper icon support.
        self.samp_client = SAMPIntegratedClient(
            metadata = {
                "samp.name":"Orange Client",
                "samp.description.text":"Orange SAMP connectivity",
                "OrangeClient.version":"0.01",
                "samp.icon.url":"http://www.astro.rug.nl/~buddel/tmp/samp.png",
           }
        )

        try:
            self.samp_client.connect()
            #self.samp_client.bind_receive_notification("table.load.votable", self.received_table_load_votable)
            self.samp_client.bind_receive_call("table.load.votable", self.received_table_load_votable_call)
            #self.SAMP_client.bind_receive_call("table.this.is.cool.table", self.table_this_is_cool_table)
            self.samp_client.bind_receive_call("target.object.highlight", self.received_target_object_highlight_call)

            self.infoa.setText("SAMP connected.")
            self.button_connect.setHidden(True)
            self.button_disconnect.setHidden(False)
        except Exception as e:
            self.infoa.setText("SAMP error: %s" % e)


    def set_region_of_interest(self, region_of_interest):
        """
        A region of interest has been indicated, probably by the user.
        Give preference to data in this region when pulling more data.
        """
        self.region_of_interest = region_of_interest


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
