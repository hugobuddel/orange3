"""
LazyTable is a data structure derived from Table that doesn't
necessarily have all the data it represents directly available.

TODO:
- Harmonize naming to the Orange naming convention.
- Think of how to use unique keys. The row_index should work, but this should
  then also be stored somewhere because X, Y and metas do not have to have
  the correct order. That is, if a widget first asks for self.data[10]
  and subsequently for self.data[5], then the first row in X will be row 10
  and the second row 5 etc.
"""

from Orange.data.table import Instance, RowInstance, Table

#class LazyRowInstance(RowInstance):
class LazyRowInstance(Instance):
    """
    LazyRowInstance is a lazy version of RowInstance.
    
    This is a very early rudimentary version.
    
    TODO:
    - Go through the 'table' to get individual cells instead of going
      directly to the widget_origin.
    """
    def __init__(self, table, row_index):
        """
        Construct a data instance representing the given row of the table.
        """
        super().__init__(table.domain)
        self.table = table
        self.row_index = row_index
    
    def __getitem__(self, key):
        """
        Returns a specific value by asking the table / widget_origin
        for the value.
        
        TODO:
        - Do not go to widget_origin directly, but go to the table
          first. The table should then cache the value in it's X/Y.
        - Check whether value is already available based on a unique key (row_index?).
        - Cache the data under a unique key if not yet available.
        """
        value = self.table.widget_origin.pull_cell(self.row_index, key)
        # TODO: where does the 'int' come from?
        if isinstance(value, int):
            value = float(value)
        self[key] = value
        return value
        
    

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

        # Ensure that the row is added to X and Y etc.
        # TODO: allow rows to have not all their attributes filled in.
        for k in self.domain:
            value = row[k]

        self.append(row)
        return row

    def len_full_data(self):
        """
        Returns the full length of the dataset. Not all this data might be initialized.
        This length can be unknown, if the full data set has not yet been derived.
        This length can also be infinite, in case an infinite generator is used to create
        this laze table.
        """
        length = self.widget_origin.pull_length()
        print("in len_full_data!", length)
        return length

    def len_instantiated_data(self):
        """
        Returns the length of the instantiated data. This is the data that is directly
        available to the widgets. The rest of the data can still be requested by accessing
        it though.
        """
        length = len(self.X)
        print("in len_instantiated_data!", length)
        return length

    take_len_of_instantiated_data = False
    def __len__(self):
        """
        There are two versions of len(), one to get the size of the dataset irrespective of how much of it is
        already available in python and one to get the size of the available data.

        The append() and insert() functions below are used to add newly instantiated rows to the already
        instantiated data. These should use the instantiated data length and not the full one.
        """
        length = self.len_instantiated_data() if self.take_len_of_instantiated_data else self.len_full_data()
        return length

    def fake_len_old(self, func, *args, **kwargs):
        """
         This does not work for some reason.
        """
        self.__len__ = self.len_instantiated_data
        return_value = func(*args, **kwargs)
        self.__len__ = self.len_full_data
        return return_value

    def fake_len(self, func, *args, **kwargs):
        """
        This is a bit of a kludge.
        """
        should_we_revert_take_len = (self.take_len_of_instantiated_data == False)
        self.take_len_of_instantiated_data = True
        return_value = func(*args, **kwargs)
        if should_we_revert_take_len:
            self.take_len_of_instantiated_data = False
        return return_value


    def append(self, *args, **kwargs):
        return self.fake_len(super().append, *args, **kwargs)

    def insert(self, *args, **kwargs):
        return self.fake_len(super().insert, *args, **kwargs)


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
        
        
        
