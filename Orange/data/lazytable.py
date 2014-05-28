"""
LazyTable is a data structure derived from Table that doesn't
necessarily have all the data it represents directly available.

TODO:
- Harmonize naming to the Orange naming convention.  
"""

from Orange.data.table import RowInstance, Table, Columns

class LazyRowInstance(RowInstance):
    """
    LazyRowInstance is a lazy version of RowInstance.
    
    This is a very early rudimentary version.
    
    TODO:
    - Add support for X, Y, metas.
    - So we can use __init__ of super()
    - Go through the 'table' to get individual cells instead of going
      directly to the widgit_origin.
    """
    def __init__(self, table, row_index):
        """
        Construct a data instance representing the given row of the table.
        """
        # Can't call super().__init__() because RowInstance uses
        # X and Y of the table, which is not yet supported.
        # TODO: Add support for X, Y etc.
        #super().__init__(table.domain)
        self.table = table
        self.row_index = row_index
    
    def __getitem__(self, key):
        """
        Returns a specific value by asking the table / widget_origin
        for the value.
        
        TODO: Do not go to widget_origin direcly, but go to the table
          first. The table should then cache the value in it's X/Y.
        """
        return self.table.widget_origin.pull_cell(self.row_index, key.name)
        
    

class LazyTable(Table):
    """
    LazyTable is a data structure derived from Table that doesn't
    necessarily have all the data it represents directly available.
    
    The LazyTable initially does not contain instantiated data.
    However, the data can be accessed as if it were a normal Table.
    Any data that is not yet available is retrieved from the widget
    that created the LazyTable.
    
    The widget_origin must be set to (and by) the widget that has
    created this LazyTable instance. widget_origin is used to pull
    data that is not yet available in this table.
    
    TODO:
    - Implement support for .X and .Y.
    - Cache the pulled data (e.g. in .X and .Y).
    - Let _compute_basic_stats return sensible values. These usually
      do not have to be exact, but this depends on the reason why
      the stats are requested.
    """
    
    widget_origin = None
    
    def __getitem__(self, index_row):
        row = LazyRowInstance(self, index_row)
        return row

    def __len__(self):
        length = self.widget_origin.pull_length()
        return length

    def has_weights(self):
        """
        Return `True` if the data instances are weighed. 
        Hacked to return False.
        """
        return False

    def X_density(self):
        return 1

    def Y_density(self):
        return 1

    def metas_density(self):
        return 1


    def _compute_basic_stats(self, include_metas=None):
        """
        _compute_basic_stats is faked.
        
        Returns a 6-element tuple or an array of shape (len(x), 6)
                Computed (min, max, mean, 0, #nans and #non-nans)
            
        TODO: Do something sensible.
        """
        stats = [ (-9000, 9000, 0.0, 0, 0, len(self)) ] * len(self.domain)
        return stats
        
        
        
