import numpy
from sklearn import linear_model
from sklearn.preprocessing import Imputer
import Orange.data
import Orange.classification
#from Orange.data.continuizer import DomainContinuizer

class SGDLearner(Orange.classification.SklLearner):

    def __init__(self, all_classes):
        self.all_classes = all_classes
        self.reset()

    def fit(self, X, Y, W):
        self.clf = self.clf.partial_fit(X, Y.reshape(-1), self.all_classes)
        # Fit some more times, see comment in partial_fit.
        return self.partial_fit(X, Y, W)

    def partial_fit(self, X, Y, W):
        for i in range(5):
            self.clf = self.clf.partial_fit(X, Y.reshape(-1))
        
        # Fit 5 times because n_iter is set to 1 for partial_fit.
        # See help of SGDClassifier:
        """
        n_iter : int, optional

        The number of passes over the training data (aka epochs). The number
        of iterations is set to 1 if using partial_fit. Defaults to 5.
        """
        return SGDClassifier(self.clf)

    def reset(self):
        # 'log' or 'modified_huber' required to predict probabilities.
        self.clf = linear_model.SGDClassifier(loss='log')

class SGDClassifier(Orange.classification.SklModel):

    def __init__(self, clf):
        self.clf = clf

    def predict(self, X):
        value = self.clf.predict(X)
        return value