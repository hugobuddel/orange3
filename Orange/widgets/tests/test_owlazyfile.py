__author__ = 'buddel'

from unittest import TestCase
from PyQt4.QtGui import QApplication

from Orange.widgets.data.owlazyfile import OWLazyFile
from Orange.widgets.settings import Setting

class OWLazyFileTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.qApp = QApplication([])

    @classmethod
    def tearDownClass(cls):
        cls.qApp.quit()

    def test_lazyfile(self):
        # TODO: how to unset recent_files ?
        #OWLazyFile.recent_files = Setting(["(none)"])
        #print(OWLazyFile.recent_files)
        #setattr(instance, setting.name, setting.default)
        #OWLazyFile.recent_files = OWLazyFile.recent_files.default
        #print(len(OWLazyFile.recent_files))
        widget = OWLazyFile()
        widget.open_file("Orange/datasets/glass.fixed")

        length_real = widget.data.len_instantiated_data()
        self.assertEqual(
            length_real,
            0,
            "Data has wrong length A: {} != {}.".format(length_real, 0)
        )

        row4a = widget.data[4]
        length_real = widget.data.len_instantiated_data()
        self.assertEqual(
            length_real,
            1,
            "Data has wrong length B: {} != {}.".format(length_real, 1)
        )

        row4b = widget.data[4]
        length_real = widget.data.len_instantiated_data()
        self.assertEqual(
            length_real,
            1,
            "Data has wrong length C: {} != {}.".format(length_real, 1)
        )

        self.assertEqual(
            row4a,
            row4b,
            "row4a != row4b",
        )


        row2a = widget.data[2]
        length_real = widget.data.len_instantiated_data()
        self.assertEqual(
            length_real,
            2,
            "Data has wrong length C: {} != {}.".format(length_real, 2)
        )


        row4c = widget.data[4]
        length_real = widget.data.len_instantiated_data()
        self.assertEqual(
            length_real,
            2,
            "Data has wrong length C: {} != {}.".format(length_real, 2)
        )

        self.assertEqual(
            row4a,
            row4c,
            "row4a != row4c",
        )




