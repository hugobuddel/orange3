from Orange.data import *

import hashlib

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
        
    def __getitem__(self, key):
      
        column_index = key
        
        row_index_bytes = self.row_index.to_bytes(8, 'little')
        column_index_bytes = column_index.to_bytes(8, 'little')
        
        hash = hashlib.sha256(row_index_bytes + column_index_bytes).hexdigest()
        
        print(hash)
        
        return Value(self._domain[key], 1.0)
      
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