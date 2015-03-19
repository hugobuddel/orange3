import numpy
from sklearn import linear_model
from sklearn.preprocessing import Imputer
import Orange.data
import Orange.classification
from Orange.data.continuizer import DomainContinuizer

class SGDLearner(Orange.classification.SklFitter):

    def __init__(self, all_classes):
        self.all_classes = all_classes
        self.reset()

    def fit(self, X, Y, W):
        return SGDClassifier(self.clf.partial_fit(X, Y.reshape(-1), self.all_classes))

    def partial_fit(self, X, Y, W):
        return SGDClassifier(self.clf.partial_fit(X, Y.reshape(-1), self.all_classes))

    def reset(self):
        self.clf = linear_model.SGDClassifier(loss='log') # 'log' or 'modified_huber' required to predict probabilities.

class SGDClassifier(Orange.classification.SklModel):

    def __init__(self, clf):
        self.clf = clf

    def predict(self, X):
        value = self.clf.predict(X)
        return value