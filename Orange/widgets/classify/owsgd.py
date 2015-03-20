import Orange.data
from Orange.classification import sgd
from Orange.widgets import widget, gui
from Orange.widgets.settings import Setting

# Just required for testing?
import numpy as np
import sklearn.linear_model
import matplotlib.pyplot as plt

def is_discrete(var):
    return isinstance(var, Orange.data.DiscreteVariable)

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

        box = gui.widgetBox(self.controlArea, "Data pulling")
        gui.spin(box, self, "no_of_instances_to_pull", 1, 100, label="Number of instances to pull")
        gui.button(self.controlArea, self, "Pull", callback=self.onPull, default=True)

        self.instancesReceived = 0
        gui.label(self.controlArea, self, "Received %(instancesReceived)i instances", box="Statistics")

        self.setMinimumWidth(250)
        layout = self.layout()
        self.layout().setSizeConstraint(layout.SetFixedSize)

        #self.apply()

        self.learner = None


    def set_data(self, data):

        if data is not None:
            print("Setting " + str(len(data)) + " instances of data...")
            self.instancesReceived = len(data)

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
        self.instancesReceived = self.instancesReceived + len(data)

        if(self.learner is None):
            # The first time we receive new data we create a learner for it.
            all_classes = np.unique(data.Y)
            self.learner = sgd.SGDLearner(all_classes)
            self.learner.name = self.learner_name

            # Train the learner.
            classifier = self.learner(data)  # Calls through to fit()
        else:
            # If we already had a learner then adapt it to the new data.
            classifier = self.learner.partial_fit(data.X, data.Y, None)
            classifier.name = self.learner.name

        # Pass it on through the network.
        self.send("Learner", self.learner)
        self.send("Classifier", classifier)

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
