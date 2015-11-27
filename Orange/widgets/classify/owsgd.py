import Orange.data
from Orange.classification import sgd
from Orange.widgets import widget, gui
from Orange.widgets.settings import Setting

import numpy as np

import matplotlib.pyplot as plt

import itertools
import sys
import threading
import copy

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt4 import QtGui
from PyQt4.QtGui import QApplication

from Orange.data.lazytable import len_lazyaware, eq_lazyaware
from Orange.data.instance import Instance

# pylint: disable=line-too-long, trailing-whitespace

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
    icon = "icons/SGD.svg"
    #inputs = [("Data", Orange.data.Table, "set_data"), ("New Data", Orange.data.Table, "set_new_data")]
    inputs = [("Data", Orange.data.Table, "set_data")]
    outputs = [
        ("Learner", sgd.SGDLearner),
        ("Classifier", sgd.SGDClassifier),
        ("self", object),
    ]
    learner_name = Setting("SGD")

    def __init__(self, parent=None):
        super().__init__(parent)

        self.data = None
        self.data_roi = None
        
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
        self.filter_roi = None

        # Pause improving the classification? Can currently only be done
        # manually. In the future this should be done when the classifier
        # has reached a certain level of quality.
        self.pause_training = False
        
        # Internal pausing of the training, e.g. when a new ROI is given.
        self._pause_training = False
                
        # TODO: Why would we set this to False?
        self.use_dynamic_bounds = True

        gui.button(self.controlArea, self, "Reset", callback=self._reset, default=True)
        #gui.button(self.controlArea, self, "Retrain", callback=self._retrain, default=True)
        #gui.button(self.controlArea, self, "Plot", callback=self._plot, default=True)
        
        gui.checkBox(self.controlArea, self, "pause_training", label="Pause Training", callback=self.on_pause_toggled)
        #gui.checkBox(self.controlArea, self, "use_dynamic_bounds", label="Use dynamic bounds")
        gui.checkBox(self.controlArea, self, "use_roi", label="Use region of interest", callback=self.on_roi_changed)

        #self.spin_min_x = gui.spin(self.controlArea, self, "roi_min_x", -1000.0, 1000.0, label="ROI Min X", callback=self.on_roi_changed)
        #self.spin_max_x = gui.spin(self.controlArea, self, "roi_max_x", -1000.0, 1000.0, label="ROI Max X", callback=self.on_roi_changed)
        #self.spin_min_y = gui.spin(self.controlArea, self, "roi_min_y", -1000.0, 1000.0, label="ROI Min Y", callback=self.on_roi_changed)
        #self.spin_max_y = gui.spin(self.controlArea, self, "roi_max_y", -1000.0, 1000.0, label="ROI Max Y", callback=self.on_roi_changed)

        gui.label(self.controlArea, self, "Trained on %(no_of_instances_trained)i instances", box="Statistics")

        self.sc = MyMplCanvas(None, width=5, height=4, dpi=100)

        self.setMinimumWidth(250)
        #layout = self.layout()
        #self.layout().setSizeConstraint(layout.SetFixedSize)

        self.mainArea.layout().addWidget(self.sc)

        self.sc.fig.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.sc.fig.canvas.mpl_connect('button_release_event', self.on_button_release)

        self.lock_on_plotting = threading.Lock()
        self.lock_on_training = threading.Lock()
        #self.lock_on_training = threading.Condition()
        #self.thread_training = None
        
        self.send("self", self)
    
    def on_pause_toggled(self):
        print("Pause Toggled")
        # This new thread will claim the lock and will subsequently check
        # self.pause_training again to determine whether to restart training.
        threading.Thread(target=self.training_thread, kwargs={'data': self.data, 'filter_roi': self.filter_roi}).start()
 
    def on_roi_changed(self, guess_roi=True):
        #self.spin_min_x.setEnabled(self.use_roi)
        #self.spin_max_x.setEnabled(self.use_roi)
        #self.spin_min_y.setEnabled(self.use_roi)
        #self.spin_max_y.setEnabled(self.use_roi)

        if self.use_roi:
            if guess_roi:
                xsbad = np.array([instance[0] for instance in self.bad_instances])
                ysbad = np.array([instance[1] for instance in self.bad_instances])

                self.roi_min_x = xsbad.mean() - 2*xsbad.std() 
                self.roi_max_x = xsbad.mean() + 2*xsbad.std()
                self.roi_min_y = ysbad.mean() - 2*ysbad.std()
                self.roi_max_y = ysbad.mean() + 2*ysbad.std()
        else:
            # TODO: allow unsetting of ROI
            self.roi_min_x = -1000.0
            self.roi_max_x = 1000.0
            self.roi_min_y = -1000.0
            self.roi_max_y = 1000.0

        f0 = Orange.data.filter.FilterContinuous(
            self.data.domain.attributes[0],
            Orange.data.filter.FilterContinuous.Between,
            min=self.roi_min_x,
            max=self.roi_max_x,
        )
        f1 = Orange.data.filter.FilterContinuous(
            self.data.domain.attributes[1],
            Orange.data.filter.FilterContinuous.Between,
            min=self.roi_min_y,
            max=self.roi_max_y,
        )
        
        filter_roi = Orange.data.filter.Values([f0, f1])
        
        # Restart training thread with new ROI.
        threading.Thread(target=self.training_thread, kwargs={'data': self.data, 'filter_roi': filter_roi}).start()
        
        # In the meantime, already plot the red rectangle.
        self._plot()
        

        

    def __del__(self):
        self._pause_training = True
        
    def set_data(self, data):
        threading.Thread(target=self.training_thread, kwargs={'data': data, 'filter_roi': None}).start()
        

    def training_thread(self, data, filter_roi, force_reset=False):
        """
        4 scenario's:
        - Data set to None. E.g. when sending widgets sends no data.
          Stop the other threads but don't do anything.
        - Data is changed or force_reset.
          Stop other threads and restart training with new data.
        - Roi is changed.
          Stop other threads. Change ROI and iterator and continue training.
        - Data and filter the same.
          Restart/continue training.
        
        Only (re)start/continue training when pause_training is not set.
        """
        
        new_data = (self.data is None) or (not eq_lazyaware(self.data, data)) or force_reset
        new_roi = not self.filter_roi == filter_roi

        print("New training thread %s %s %s %s %s" % (data is None, filter_roi is None, new_data, new_roi, force_reset))
        
        # Pause training to signal the other threads to stop and release the
        # lock
        self._pause_training = True
        with self.lock_on_training:
            if data is None:
                # We got the training lock, now we unset data.
                self.data = None
                # TODO: Save the ROI?
                self.filter_roi = None
                self.data_roi = None
                self.iterator_data = None
            else:
                if new_data or new_roi:
                    self.data = data
                    self.filter_roi = filter_roi
                    self.data_roi = self.filter_roi(self.data) if filter_roi else self.data
                    # TODO: Now it will restart from 0?
                    self.iterator_data = iter(self.data_roi)
                
                if new_data:
                    # We're received a new data set so create a new learner to replace
                    # any existing one
                    print("Setting new data with " + str(len_lazyaware(data)) + " instances.")

                    self.get_statistics()
                    self.learner = sgd.SGDLearner(self.all_classes, self.means, self.stds)
                    self.learner.name = self.learner_name
                    
                    # Reset the trained instances.
                    self.instances_trained = Orange.data.Table.from_domain(self.data.domain)
                    self.no_of_instances_trained = 0
                
                # Start training.
                self._pause_training = self.pause_training
                while not self._pause_training:
                    self.train()

        
    def train(self):
        """
        Performs three actions:
        1) Fetches some new instances.
        2) Improves the trainer using these instances.
        3) Sends the improved trainer.
        """
        new_instances = Orange.data.Table.from_domain(self.data.domain)
        #for instance in itertools.islice(self.iterator_data, 20):
        #for i,instance in enumerate(itertools.islice(self.iterator_data, 20)):
        for i,instance in enumerate(itertools.islice(self.iterator_data, 20)):
            # Copy the instance to prevent changing the original.
            instance = Instance(next(self.iterator_data))
            new_instances.append(instance)
            self.instances_trained.append(instance)

        if len(new_instances):
            print("And learn some more")
            # TODO: Can we do without accessing .X and .Y?
            classifier = self.learner.partial_fit(new_instances.X, new_instances.Y, None)
        else:
            print("Got all instances!")
            self._pause_training = True
            return
        
        classifier.name = self.learner.name
        
        self.no_of_instances_trained = len(self.instances_trained)

        # Deepcopy learner and classifier because the testing widget might
        # modify the learner while we are still improving it.
        self.learner_send = sgd.SGDLearner(self.all_classes, self.means, self.stds)
        self.learner_send.clf = copy.deepcopy(self.learner.clf)
        self.classifier_send = sgd.SGDClassifier(copy.deepcopy(classifier.clf))
        
        # Try and except block around the sending. To prevent sending when
        # Orange is closing down.
        # TODO: A better way to achieve this.
        #self.send("Learner", self.learner_send)
        #self.send("Classifier", self.classifier_send)
        try:
            self.send("Learner", self.learner_send)
            self.send("Classifier", self.classifier_send)
        except RuntimeError as e:
            if str(e) == "wrapped C/C++ object of type WidgetsSignalManager has been deleted":
                print("Exception in sending, shutting down? %s %s" % (self.pause_training, self._pause_training))
                self._pause_training = True
            else:
                raise(e)
                
        self._plot()

        
        
    def on_button_press(self, event):
        print('Press button=%s, x=%s, y=%s, xdata=%s, ydata=%s'%(
            event.button, event.x, event.y, event.xdata, event.ydata))
        self.x_press = event.xdata
        self.y_press = event.ydata

    def on_button_release(self, event):
        print('Release button=%s, x=%s, y=%s, xdata=%s, ydata=%s'%(
            event.button, event.x, event.y, event.xdata, event.ydata))
        self.x_release = event.xdata
        self.y_release = event.ydata

        # In some scenarios xdata and ydata are None.
        if (self.x_press is not None) and (self.y_press is not None) and (self.x_release is not None) and (self.y_release is not None):
            self.roi_min_x = min(self.x_press, self.x_release)
            self.roi_max_x = max(self.x_press, self.x_release)
            self.roi_min_y = min(self.y_press, self.y_release)
            self.roi_max_y = max(self.y_press, self.y_release)
            
            # Reset the press and release.
            self.x_press = None
            self.y_press = None
            self.x_release = None
            self.y_release = None

            # Turn roi on.
            self.use_roi = True

            self.on_roi_changed(guess_roi=False)


    def _plot(self):
        if self.lock_on_plotting.acquire(timeout=1):
            self._actually_plot()
            self.lock_on_plotting.release()
        else:
            print("Unable to comply, plotting in progress.")

    def _actually_plot(self):

        self.sc.fig.clf()

        if len(self.instances_trained) > 0:

            # Copy X and Y because they might be updated while plotting.
            X = self.instances_trained.X.copy()
            Y = self.instances_trained.Y.copy()
            
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

                Zh = np.array([
                    self.learner.decision_function([
                        x1,
                        x2,
                    ])[0]
                    for x1,x2 in zip(np.ravel(X1), np.ravel(X2))
                ])
                Z = Zh.reshape(X1.shape)

                # Attempts to create more insightful levels.
                #level1 = abs(Z).sum()/Z.size
                #level1 = Z.sum()/Z.size
                #levels = [-level1, 0.0, level1]
                levels = [-1.0, 0.0, 1.0]
                linestyles = ['dashed', 'solid', 'dashed']
                colors = 'k'

                self.sc.axes.contour(X1, X2, Z, levels, colors=colors, linestyles=linestyles)
                self.sc.axes.scatter(X[:, 0], X[:, 1], c=Y, cmap=plt.cm.Set3)

                # Estimate the region of interest. That is, the region in which
                # many instances are classified incorrectly.
                
                # TODO: make this more robust.
                #  - E.g. minimum n.o.instances
                #  - Perhaps enlarge?
                # TODO: integrate in GUI
                # TODO: actually propagate this ROI in some way.
                #  - With button press? to prevent SAMP congestion?
                self.bad_instances = [
                    instance for instance in self.instances_trained
                    if self.learner.predict(
                        [instance[0], instance[1]]
                    ) != instance.y
                ]

                xsbad = np.array([instance[0] for instance in self.bad_instances])
                ysbad = np.array([instance[1] for instance in self.bad_instances])

                self.sc.axes.scatter(xsbad, ysbad, c='red', marker='o')
                
                if self.use_roi:
                    self.sc.axes.plot(
                        [self.roi_min_x, self.roi_max_x, self.roi_max_x, self.roi_min_x, self.roi_min_x],
                        [self.roi_min_y, self.roi_min_y, self.roi_max_y, self.roi_max_y, self.roi_min_y],
                        color = 'r', linewidth=2.0,
                    )

            else:
                # Unsupported code for multiple attributes.
                raise NotImplementedError("Multiple attributes are not yet supported.")
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
    
    def get_statistics(self):
        """
        Get the different classes from the data.
        Also gets the mean and standard deviation from the data.
        
        Ideally (in the future?) this
        should be asked (pulled) from the data directly, but this is not (yet?)
        possible. Similarly to minima and maxima for the columns. Therefore,
        we cheat.
        """
        # First get some rows.
        for row in itertools.islice(self.data, 20):
            pass
        
        # Get the unique classes.
        self.all_classes = np.unique(self.data.Y)
        self.means = self.data.X.mean(axis=0)
        self.stds = self.data.X.std(axis=0)
    
    def _reset(self):
        threading.Thread(
            target=self.training_thread, kwargs={
                'data': self.data,
                'filter_roi': None,
                'force_reset': True,
            }
        ).start()
    
    def onDeleteWidget(self):
        """
        Stop training when the widget is deleted.
        """
        self._pause_training = True
        super().onDeleteWidget()
        # TODO: Perhaps wait for the other threads?
        
        
        
def test_main(argv=None):
    # TODO: Create a true test.
    if argv is None:
        argv = sys.argv
    argv = list(argv)
    a = QApplication(argv)
    #if len(argv) > 1:
    #    filename = argv[1]
    #else:
    #    filename = "iris"

    ow = OWSGD()
    ow.show()
    ow.raise_()
    #data = Orange.data.Table(filename)
    #ow.set_data(data)
    #ow.set_subset_data(data[:30])
    #ow.handleNewSignals()

    rval = a.exec()

    #ow.set_data(None)
    #ow.set_subset_data(None)
    #ow.handleNewSignals()
    ow.saveSettings()
    ow.onDeleteWidget()

    return rval

if __name__ == "__main__":
    test_main()
