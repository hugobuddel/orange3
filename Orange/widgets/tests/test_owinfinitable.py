import unittest
from unittest import TestCase
from PyQt4.QtGui import QApplication

from Orange.widgets.data.infinitable import OWInfiniTable

class OWInfiniTableCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.qApp = QApplication([])

    @classmethod
    def tearDownClass(cls):
        cls.qApp.quit()

    def test_lazytable(self):
        widget1 = OWInfiniTable()
        widget1.data.stop_pulling = True
        print(widget1.data.X.shape)

        widget2 = OWInfiniTable()
        widget2.data.stop_pulling = True
        print(widget2.data.X.shape)

        print(widget1.data.X)
        widget1.data.extend(widget2.data)

        print(widget1.data.X)


if __name__ == '__main__':
    #unittest.main()
    qApp = QApplication([])
    widget1 = OWInfiniTable()
    widget1.data.stop_pulling = True
    print(widget1.data.X.shape)

    widget2 = OWInfiniTable()
    widget2.data.stop_pulling = True
    print(widget2.data.X.shape)

    print(widget1.data.X)
    widget1.data.extend(widget2.data)
    #for row in widget2.data:
    #    widget1.data.append(row)

    print(widget1.data.X)
