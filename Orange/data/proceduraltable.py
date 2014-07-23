from Orange.data import *

import random
import numpy as np

"""
ProceduralTable is a Table which doesn't actually store data itself, but generates it on demand.
It can be used to simulate tables with an infinite amount of data.
"""
class ProceduralRowInstance(RowInstance):
    def __init__(self, table, row_index):
        """
        Construct a data instance representing the given row of the table.
        """
        super().__init__(table, row_index)
        
        #self._values = None
        #self._metas = None
        #self._weight = None
        
    def __getitem__(self, key):
        
        # Properties of the distribution are defined by the column name.
        random.seed(key)
        mu = random.random() * 10.0
        sigma = random.random()
 
        # The resulting value is determined by the row.
        random.seed(self.row_index)
        result = random.gauss(mu, sigma)

        return Value(self._domain[key], result)
      
    @property
    def x(self):
        """
        Instance's attributes as a 1-dimensional numpy array whose length
        equals len(self.domain.attributes)
        """
        result = np.zeros(len(self.domain.attributes))
        for (i, val) in enumerate(result):
            result[i] = self[i]
        return result
      
    
    # This has been copied from Instance, and changed to print 'x' and 'y'
    # instead of '_x' and 'y' as the former have ben correctly overloaded.
    def __str__(self):
        s = "[" + self.str_values(self.x, self._domain.attributes)
        if self._domain.class_vars:
            s += " | " + self.str_values(self.y, self._domain.class_vars)
        s += "]"
        if self._domain.metas:
            s += " {" + self.str_values(self.metas, self._domain.metas) + "}"
        return s

    __repr__ = __str__
      
class ProceduralTable(Table):
  
    def __getitem__(self, key):

        print("Creating instance")
        return ProceduralRowInstance(self, key)
    
        
if __name__ == '__main__':
    a = ContinuousVariable("Var A")
    b = ContinuousVariable("Var B")
    c = DiscreteVariable('number', ('one', 'two', 'three'))
    
    dom = Domain([a,b], c)
    
    inst = Instance(dom)
    inst[0] = 12.5
    inst[1] = 17.4
    inst.set_class('one')
    
    tab = ProceduralTable.from_domain(dom, 10)
    #tab.append(inst);
    
    print(tab)