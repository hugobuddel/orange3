from Orange.data import *

"""
ProceduralTable is a Table which doesn't actually store data itself, but generates it on demand.
It can be used to simulate tables with an infinite amount of data.
"""
class ProceduralInstance(Instance):
    def __init__(self, domain):
        """
        Construct a data instance representing the given row of the table.
        """
        super().__init__(domain)
        
if __name__ == '__main__':
    a = ContinuousVariable()
    b = ContinuousVariable()
    c = DiscreteVariable('number', ('one', 'two', 'three'))
    dom = Domain([a,b], c)
    instance = ProceduralInstance(dom)
    instance[0] = 12.5
    instance[1] = 17.4
    instance.set_class('one')
    print(instance)