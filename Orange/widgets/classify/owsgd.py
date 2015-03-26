import Orange.data
from Orange.classification import sgd
from Orange.widgets import widget, gui
from Orange.widgets.settings import Setting

# Just required for testing?
import numpy as np
import sklearn.linear_model
import matplotlib.pyplot as plt

from numpy import arange, sin, pi

from matplotlib.backends import qt4_compat
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

use_pyside = qt4_compat.QT_API == qt4_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore

import random

def is_discrete(var):
    return isinstance(var, Orange.data.DiscreteVariable)

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)

        self.compute_initial_figure()

        #
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""
    def compute_initial_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.axes.plot(t, s)

class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""
    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        #timer = QtCore.QTimer(self)
        #timer.timeout.connect(self.update_figure)
        #timer.start(1000)

    def compute_initial_figure(self):
        self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')
        self.axes.plot([5, 4, 7, 1], [5, 6, 7, 1], 'r')

    #def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
    #    l = [random.randint(0, 10) for i in range(4)]

    #    self.axes.plot([0, 1, 2, 3], l, 'r')
    #    self.draw()

class OWSGD(widget.OWWidget):

    name = "Stochastic Gradient Descent"
    description = "Stochastic Gradient Descent"
    #icon = "icons/KNN.svg"
    inputs = [("Data", Orange.data.Table, "set_data"), ("New Data", Orange.data.Table, "set_new_data")]
    outputs = [("Learner", sgd.SGDLearner), ("Classifier", sgd.SGDClassifier)]

    want_main_area = False
    learner_name = Setting("SGD")

    def __init__(self, parent=None):
        super().__init__(parent)

        self.learner = None
        self.instances_received = None
        self.no_of_instances_received = 0

        box = gui.widgetBox(self.controlArea, "Data pulling")
        gui.spin(box, self, "no_of_instances_to_pull", 1, 100, label="Number of instances to pull")
        gui.button(self.controlArea, self, "Pull", callback=self.onPull, default=True)

        gui.button(self.controlArea, self, "Plot", callback=self.onPlot)
        gui.button(self.controlArea, self, "Plot 2", callback=self.onPlot2)

        gui.label(self.controlArea, self, "Received %(no_of_instances_received)i instances", box="Statistics")

        self.sc = MyDynamicMplCanvas(self.controlArea, width=5, height=4, dpi=100)

        self.setMinimumWidth(250)
        layout = self.layout()
        self.layout().setSizeConstraint(layout.SetFixedSize)

        self.layout().addWidget(self.sc)





    def set_data(self, data):

        if data is not None:
            print("Setting " + str(len(data)) + " instances of data...")
            self.instances_received = data
            self.no_of_instances_received = len(self.instances_received)

            # We're received a new data set so create a new learner to replace any existing one
            all_classes = np.unique(data.Y)
            self.learner = sgd.SGDLearner(all_classes)
            self.learner.name = self.learner_name

            # Train the learner.
            classifier = self.learner(data)  # Calls through to fit()

            # Pass it on through the network.
            self.send("Learner", self.learner)
            self.send("Classifier", classifier)
            
    def set_new_data(self, data):

      if data is not None:
        print("Setting " + str(len(data)) + " instances of new data...")

        if(self.learner is None):
            self.instances_received = data

            # The first time we receive new data we create a learner for it.
            all_classes = np.unique(data.Y)
            self.learner = sgd.SGDLearner(all_classes)
            self.learner.name = self.learner_name

            # Train the learner.
            classifier = self.learner(data)  # Calls through to fit()
        else:
            self.instances_received.extend(data)

            # If we already had a learner then adapt it to the new data.
            classifier = self.learner.partial_fit(data.X, data.Y, None)
            classifier.name = self.learner.name

        self.no_of_instances_received = len(self.instances_received)

        self.onPlot()

        # Pass it on through the network.
        self.send("Learner", self.learner)
        self.send("Classifier", classifier)

    def onPlot2(self):
        print("Doing plot 2")
        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.plot([1,2,3])
        ax.set_title('hi mom')
        ax.grid(True)
        ax.set_xlabel('time')
        ax.set_ylabel('volts')
        canvas.print_figure('test')

    def onPlot(self):
        X = self.instances_received.X
        Y = self.instances_received.Y

        x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
        y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1

        # plot the line, the points, and the nearest vectors to the plane
        xx = np.linspace(x_min, x_max, 10)
        yy = np.linspace(y_min, y_max, 10)

        X1, X2 = np.meshgrid(xx, yy)
        Z = np.empty(X1.shape)
        for (i, j), val in np.ndenumerate(X1):
            x1 = val
            x2 = X2[i, j]
            p = self.learner.clf.decision_function([x1, x2])
            Z[i, j] = p[0]
        levels = [-1.0, 0.0, 1.0]
        linestyles = ['dashed', 'solid', 'dashed']
        colors = 'k'
        #plt.contour(X1, X2, Z, levels, colors=colors, linestyles=linestyles)
        #plt.scatter(X[:, 0], X[:, 1], c=Y, cmap=plt.cm.Paired)

        #plt.axis('tight')
        #plt.show()

        self.sc.axes.cla()
        self.sc.axes.hold(True)
        self.sc.axes.contour(X1, X2, Z, levels, colors=colors, linestyles=linestyles)
        self.sc.draw()
        self.sc.axes.scatter(X[:, 0], X[:, 1], c=Y, cmap=plt.cm.Paired)
        self.sc.draw()

        #l = [random.randint(0, 10) for i in range(4)]
        #self.sc.axes.plot([0, 1, 2, 3], l, 'r')
        #l = [random.randint(0, 10) for i in range(4)]
        #self.sc.axes.plot([0, 1, 2, 3], l, 'g')
        #self.sc.draw()

    #def apply(self):
    #    classifier = None
    #    if self.data is not None:
    #        classifier = self.learner(self.data)
    #        classifier.name = self.learner.name

    #    self.send("Learner", self.learner)
    #    self.send("Classifier", classifier)

    ################################################################################
    # Tests for pulling/partial_fit functionality
    ################################################################################
    no_of_instances_to_pull = Setting(10)
    current_instance_index = 0
    clf = sklearn.linear_model.SGDClassifier()

    def onPull(self):
        print("Pulling {0} items".format(self.no_of_instances_to_pull))
        begin = self.current_instance_index
        end = begin + self.no_of_instances_to_pull
        self.current_instance_index = self.current_instance_index + self.no_of_instances_to_pull

        pulled_X = self.data.X[begin : end]
        pulled_Y = self.data.Y[begin : end]
        pulled_Y = np.reshape(pulled_Y, -1)

        pulled = self.data[begin : end]

        #print(type(pulled_X), type(pulled_Y))
        #print(pulled_X, pulled_Y)
        all_classes = np.unique(self.data.Y)
        self.clf.partial_fit(pulled_X, pulled_Y, all_classes)

        pulled_to_date_X = self.data.X[:self.current_instance_index]
        pulled_to_date_Y = self.data.Y[:self.current_instance_index]

        h = 0.02
        x_min, x_max = pulled_to_date_X[:, 0].min() - 1, pulled_to_date_X[:, 0].max() + 1
        y_min, y_max = pulled_to_date_X[:, 1].min() - 1, pulled_to_date_X[:, 1].max() + 1
        xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                     np.arange(y_min, y_max, h))

        Z = self.clf.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)
        plt.contourf(xx, yy, Z, cmap=plt.cm.Paired, alpha=0.8)

        plt.scatter(pulled_to_date_X[:, 0], pulled_to_date_X[:, 1], c=pulled_to_date_Y, cmap=plt.cm.Paired)
        plt.show()

        classifier = None
        if self.data is not None:
            classifier = self.learner(pulled)
            classifier.name = self.learner.name

        self.send("Learner", self.learner)
        self.send("Classifier", classifier)
