import Orange.data
from Orange.classification import sgd
from Orange.widgets import widget, gui
from Orange.widgets.settings import Setting

# Just required for testing?
import numpy as np
import sklearn.linear_model

import matplotlib.pyplot as plt

from numpy import arange, sin, pi

import itertools

import threading

from matplotlib.backends import qt4_compat
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

use_pyside = qt4_compat.QT_API == qt4_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore

def is_discrete(var):
    return isinstance(var, Orange.data.DiscreteVariable)

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        #
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class OWSGD(widget.OWWidget):

    name = "Stochastic Gradient Descent"
    description = "Stochastic Gradient Descent"
    #icon = "icons/KNN.svg"
    #inputs = [("Data", Orange.data.Table, "set_data"), ("New Data", Orange.data.Table, "set_new_data")]
    inputs = [("Data", Orange.data.Table, "set_data")]
    outputs = [("Learner", sgd.SGDLearner), ("Classifier", sgd.SGDClassifier)]
    learner_name = Setting("SGD")

    def __init__(self, parent=None):
        super().__init__(parent)

        self.learner = None
        self.instances_trained = None
        self.no_of_instances_trained = 0

        self.x_press = None
        self.y_press = None
        self.x_release = None
        self.y_release = None

        # TODO: Make ROI implicit.
        self.use_roi = False
        # TODO: Replace ROI with a Filter
        self.roi_min_x = -2.0
        self.roi_max_x = 2.0
        self.roi_min_y = -2.0
        self.roi_max_y = 2.0

        # TODO: This should be implicit.
        self.use_pull_data = False
        
        # TODO: Why would we set this to False?
        self.use_dynamic_bounds = True

        # box = gui.widgetBox(self.controlArea, "Data pulling")
        # gui.spin(box, self, "no_of_instances_to_pull", 1, 100, label="Number of instances to pull")
        gui.button(self.controlArea, self, "Reset", callback=self._reset, default=True)
        #gui.button(self.controlArea, self, "StartPulling", callback=self.onStartPulling, default=True)
        #gui.button(self.controlArea, self, "StopPulling", callback=self.onStopPulling, default=True)
        gui.button(self.controlArea, self, "Plot", callback=self._plot, default=True)

        gui.checkBox(self.controlArea, self, "use_pull_data", label="Pull data", callback=self.on_pull_toggled)
        gui.checkBox(self.controlArea, self, "use_dynamic_bounds", label="Use dynamic bounds")
        gui.checkBox(self.controlArea, self, "use_roi", label="Use region of interest", callback=self.on_roi_changed)

        self.spin_min_x = gui.spin(self.controlArea, self, "roi_min_x", -1000.0, 1000.0, label="ROI Min X", callback=self.on_roi_changed)
        self.spin_max_x = gui.spin(self.controlArea, self, "roi_max_x", -1000.0, 1000.0, label="ROI Max X", callback=self.on_roi_changed)
        self.spin_min_y = gui.spin(self.controlArea, self, "roi_min_y", -1000.0, 1000.0, label="ROI Min Y", callback=self.on_roi_changed)
        self.spin_max_y = gui.spin(self.controlArea, self, "roi_max_y", -1000.0, 1000.0, label="ROI Max Y", callback=self.on_roi_changed)
        self.on_roi_changed() # Set up initial state

        gui.label(self.controlArea, self, "Received %(no_of_instances_trained)i instances", box="Statistics")

        self.sc = MyMplCanvas(None, width=5, height=4, dpi=100)

        self.setMinimumWidth(250)
        layout = self.layout()
        self.layout().setSizeConstraint(layout.SetFixedSize)

        self.mainArea.layout().addWidget(self.sc)

        self.sc.fig.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.sc.fig.canvas.mpl_connect('button_release_event', self.on_button_release)

    def on_pull_toggled(self):
        if self.use_pull_data:
            self.pull_data()

    def on_roi_changed(self):

        self.spin_min_x.setEnabled(self.use_roi)
        self.spin_max_x.setEnabled(self.use_roi)
        self.spin_min_y.setEnabled(self.use_roi)
        self.spin_max_y.setEnabled(self.use_roi)

        roi = None
        if self.use_roi:
            roi = {'a':(self.roi_min_x, self.roi_max_x), 'b':(self.roi_min_y, self.roi_max_y)}
        else:
            roi = {'a':(-1000.0, 1000.0), 'b':(-1000.0, 1000.0)}

        try:
            self.data.set_region_of_interest(roi)
            self._plot()
        except:
            pass

    def __del__(self):
        self.do_pulling = False

    def set_data(self, data):
        # TODO: Check whether data is the same.
        if data is not None:
        
            print("Setting new data with " + str(len(data)) + " instances.")

            self.data = data
            self.iterator_data = iter(self.data)
            self._reset()
        else:
            print("Data removed")

    def pull_data(self):
        
        new_instances = Orange.data.Table.from_domain(self.data.domain)
        for instance in itertools.islice(self.iterator_data, 5):
            instance = next(self.iterator_data)
            new_instances.append(instance)
            self.instances_trained.append(instance)

        self.no_of_instances_trained = len(self.instances_trained)

        # TODO: Can we do without accessing .X and .Y?
        classifier = self.learner.partial_fit(new_instances.X, new_instances.Y, None)
        classifier.name = self.learner.name

        self.send("Learner", self.learner)
        self.send("Classifier", classifier)

        self._plot()

        if self.use_pull_data:
            threading.Timer(4, self.pull_data).start()

    def on_button_press(self, event):
        print('Press button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
            event.button, event.x, event.y, event.xdata, event.ydata))
        self.x_press = event.xdata
        self.y_press = event.ydata

    def on_button_release(self, event):
        print('Release button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
            event.button, event.x, event.y, event.xdata, event.ydata))
        self.x_release = event.xdata
        self.y_release = event.ydata

        self.roi_min_x = min(self.x_press, self.x_release)
        self.roi_max_x = max(self.x_press, self.x_release)
        self.roi_min_y = min(self.y_press, self.y_release)
        self.roi_max_y = max(self.y_press, self.y_release)

        self.use_roi = True

        self.on_roi_changed()

    def _plot(self):

        self.sc.fig.clf()

        if len(self.instances_trained) > 0:

            X = self.instances_trained.X
            Y = self.instances_trained.Y

            no_of_attributes = len(X[0])

            if no_of_attributes <= 2:

                self.sc.axes = self.sc.fig.add_subplot(1, 1, 1)

                if(self.use_dynamic_bounds == False):
                    # Limits appropriate for sample Infinitable data.
                    self.sc.axes.set_xlim([-5, 10])
                    self.sc.axes.set_ylim([-5, 3])

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

                self.sc.axes.contour(X1, X2, Z, levels, colors=colors, linestyles=linestyles)
                self.sc.axes.scatter(X[:, 0], X[:, 1], c=Y, cmap=plt.cm.Paired)

                if self.use_roi:
                    # Draw the region of interest.
                    self.sc.axes.plot([self.roi_min_x, self.roi_min_x], [self.roi_min_y,self.roi_max_y], color = 'g')
                    self.sc.axes.plot([self.roi_max_x, self.roi_max_x], [self.roi_min_y,self.roi_max_y], color = 'g')

                    self.sc.axes.plot([self.roi_min_x, self.roi_max_x], [self.roi_min_y,self.roi_min_y], color = 'g')
                    self.sc.axes.plot([self.roi_min_x, self.roi_max_x], [self.roi_max_y,self.roi_max_y], color = 'g')

            else:

                for x_pos, y_pos in itertools.product(range(no_of_attributes), repeat=2):

                    subplot_pos = x_pos + y_pos * no_of_attributes + 1 # Plus one because subplot indices start at 1.
                    self.sc.axes = self.sc.fig.add_subplot(no_of_attributes, no_of_attributes, subplot_pos)

                    if x_pos != y_pos:
                        self.sc.axes.scatter(X[:, x_pos], X[:, y_pos], c=Y, cmap=plt.cm.Paired)
                    else:
                        self.sc.axes.xaxis.set_visible(False)
                        self.sc.axes.yaxis.set_visible(False)
                        self.sc.axes.annotate(str(x_pos), (0.5, 0.5), xycoords='axes fraction', ha='center', va='center')
            self.sc.draw()

    ################################################################################
    # Tests for pulling/partial_fit functionality
    ################################################################################
    no_of_instances_to_pull = Setting(10)
    current_instance_index = 0
    clf = sklearn.linear_model.SGDClassifier()
    
    def get_classes(self):
        """
        Get the different classes from the data. Ideally (in the future?) this
        should be asked (pulled) from the data directly, but this is not (yet?)
        possible. Similarly to minima and maxima for the columns. Therefore,
        we cheat.
        """
        # First get some rows.
        for row in itertools.islice(self.data, 10):
            pass
        
        # Get the unique classes.
        all_classes = np.unique(self.data.Y)
        return all_classes
        
        
    
    def _reset(self):
        self.learner = None
        classifier = None
        
        # We're received a new data set so create a new learner to replace any existing one
        all_classes = self.get_classes()
        self.learner = sgd.SGDLearner(all_classes)
        self.learner.name = self.learner_name

        # TODO: Replace this below simply with 'pulling' more data.
        self.instances_trained = Orange.data.Table.from_domain(self.data.domain)
        for instance in itertools.islice(self.iterator_data, 5):
            self.instances_trained.append(instance)
        
        self.no_of_instances_trained = len(self.instances_trained)
        
        # Train the learner.
        classifier = self.learner(self.instances_trained)  # Calls through to fit()
        
        self.pull_data()

        # Update the plot as well.
        self._plot()

        self.send("Learner", self.learner)
        self.send("Classifier", classifier)
