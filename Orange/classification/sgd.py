import numpy
from sklearn import linear_model
from sklearn.preprocessing import Imputer
import Orange.data
import Orange.classification
#from Orange.data.continuizer import DomainContinuizer

class SGDLearner(Orange.classification.SklLearner):

    def __init__(self, all_classes, means=None, stds=None):
        self.all_classes = all_classes
        # The SGD Learner works significantly better with normalized data.
        # However, we cannot get the normalization from the data because we
        # do partial fitting. So it has to be provided.
        self.means = means
        self.stds = stds
        self.clf = linear_model.SGDClassifier(loss='log')
        self.clf.means = self.means
        self.clf.stds = self.stds

        #self.reset()

    def partial_fit(self, X, Y, W, normalize=True):
        X = X.copy()
        if normalize:
            if self.means is not None:
                X -= self.means
            if self.stds is not None:
                X /= self.stds
        
        self.clf = self.clf.partial_fit(X, Y.reshape(-1), self.all_classes)
        
        return SGDClassifier(self.clf)
    
    # TODO: Remove fit completely?
    fit = partial_fit

    # TODO: Is this reset function necessary?
    def reset(self):
        # 'log' or 'modified_huber' required to predict probabilities.
        self.clf = linear_model.SGDClassifier(loss='log')
        self.clf.means = self.means
        self.clf.stds = self.stds
    
    def decision_function(self, X):
        if self.means is not None and self.stds is not None:
            Xa = (numpy.array(X)-numpy.array(self.means))/numpy.array(self.stds)
        else:
            Xa = X
        
        value = self.clf.decision_function(Xa)
        return value

    def predict(self, X):
        if self.means is not None and self.stds is not None:
            Xa = (numpy.array(X)-numpy.array(self.means))/numpy.array(self.stds)
        else:
            1/0
            Xa = X
        
        value = self.clf.predict(Xa)
        return value
        

class SGDClassifier(Orange.classification.SklModel):

    def __init__(self, clf):
        self.clf = clf

    def predict(self, X):
        if self.clf.means is not None and self.clf.stds is not None:
            Xa = (numpy.array(X)-numpy.array(self.clf.means))/numpy.array(self.clf.stds)
        else:
            Xa = X
        
        value = self.clf.predict(Xa)
        return value
        