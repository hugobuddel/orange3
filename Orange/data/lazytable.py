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
from Orange.data.value import Value
from Orange.data.variable import Variable

import numpy

class LazyRowInstance(RowInstance):
#class LazyRowInstance(Instance):
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
        row_index is the real row of the data set, which might not be the
        materialized row
        """
        row_index_full = row_index
        row_index_materialized = table.row_mapping.get(row_index_full, None)
        if row_index_materialized is None:
            # Need to add the row to X, Y and metas. We first
            # instantiate a normal Instance because it has no row number
            # yet. The new row number will be the length of the table.
            row_index_materialized = table.len_instantiated_data()
            instance_nonrow = Instance(table.domain)
            instance_nonrow.table = table
            table.append(instance_nonrow)
            table.row_mapping[row_index_full] = row_index_materialized


        super().__init__(table, row_index_materialized)
        self.table = table
        #self.row_index = row_index
        self.row_index_full = row_index_full
        self.row_index_materialized = row_index_materialized
        # Need to set the row_index to row_index_materialized so the
        # functions in RowInstance still work.
        self.row_index = self.row_index_materialized

    
    def __getitem__(self, key):
        """
        Returns a specific value by asking the table
        for the value.
        
        TODO:
        - Add support for Y and metas.
        - Do the conversion to Value properly.
        """
        if isinstance(key, str):
            #keyid = [i for (i,k) in enumerate(self.table.domain.variables) if k.name == key][0]
            keyid = [i for (i,k) in enumerate(self.table.domain) if k.name == key][0]
            key = self.table.domain.variables[keyid]
        elif isinstance(key, int):
            keyid = key
            #key = self.table.domain.variables[keyid]
            key = self.table.domain[keyid]
        else:
            #keyid = [i for (i,k) in enumerate(self.table.domain.variables) if k == key][0]
            keyid = [i for (i,k) in enumerate(self.table.domain) if k == key][0]
            keyids_variables = [i for (i,k) in enumerate(self.table.domain.variables) if k == key]
            keyid_variables = keyids_variables[0] if len(keyids_variables) else None

        #print(keyid, keyid_variables, len(self._values), self._values.shape, self._values)
        value = self._values[keyid]
        # A nan means the value is not yet available.
        if not numpy.isnan(value):
            pass
        else:
            value = self.table.widget_origin.pull_cell(self.row_index_full, key)
            # TODO: where does the 'int' come from?
            if isinstance(value, (int, numpy.float)):
                value = float(value)

            # Cache the value both in this RowInstance as well as in
            # the original table. E.g. __str__() uses self.table.X.
            # TODO: Can we do everything with only self.table.X?
            self._values[keyid] = value
            # TODO: Ensure Y and metas are supported.
            if keyid_variables is not None:
                if keyid_variables < self.table.X.shape[1]:
                    #self.table.X[self.row_index_materialized][keyid] = value
                    self.table.X[self.row_index_materialized][keyid_variables] = value

        # TODO: convert to Value properly, see __getitem__ in Instance
        val = Value(key, value)

        return val
        
    

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

    # The widget_origin has created this LazyTable. It is used to
    # 1) pull data that is not yet available and
    # 2) resend this data to other widgets if new data is available.
    #
    # Data pulling (1) might better be implemented in another way. At the
    # moment, the LazyTable has to ask widget_origin for more data. It
    # might be better if widget_origin tells the LazyTable instance how
    # it should retrieve more data itself. That has two benefits:
    # - the LazyTable instance is more self-contained and
    # - it will be easier for widget_origin to have multiple outputs.
    #
    # Resending data (2) is not yet implemented at all.
    widget_origin = None

    # row_mapping is a dictionary that maps other identifiers to rows of
    # .X, .Y and .metas. This is necessary because the rows might be fetched
    # in non-sequential order. That is, if row 10 is requested first (e.g.
    # by table[10]), then the first row in X, Y and metas refers to row
    # 10 in the table.
    row_mapping = None

    # TODO: this seems ugly, overloading __new__
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        # No rows to map yet.
        self.row_mapping = {}
        return self


    def __init__(self, *args, **kwargs):
        # No rows to map yet.
        self.row_mapping = {}
        super().__init__(*args, **kwargs)

    def __getitem__(self, index_row):
        if isinstance(index_row, int):
            # Just a normal row.
            row = LazyRowInstance(self, index_row)

            # Ensure that the row is added to X and Y etc.
            # TODO: allow rows to have not all their attributes filled in.
            for k in self.domain:
                value = row[k]
            return row
        elif isinstance(index_row, numpy.ndarray):
            # Apparently this is a mask.
            # TODO: Do what should be done here, see documentation of
            #   tabular data classes.
            #row_mapping_inverse = self.row_mapping_full_from_materialized()
            # Not sure what to return, probably a new LazyTable.
            return self
        elif isinstance(index_row, slice):
            # TODO: decide whether these are materialized or full row_indices.
            start = index_row.start if index_row.start is not None else 0
            stop = index_row.stop if index_row.stop is not None else self.len_instantiated_data()
            step = index_row.step if index_row.step is not None else 1
            row_indices_materialized = list(range(start, stop, step))
            # TODO: slice the table. Probably need to return a new table?
            return self

    def __str__(self):
        """
        Overloaded because table.__str__ performs slicing which is not yet
        supported.
        """
        return "Some LazyTable!"

    def checksum(self):
        """
        Overloaded because widgets might check whether the send data has the
        same checksum as the data they already have. However, the lazy
        widgets keep sending the same data instance, except with more data.
        So those checking widgets will compare the same object with itself.

        TODO: find a proper solution to this, because the legitimate uses
        of checksum are also disabled.
        """
        return numpy.random.randint(10000000)


    def row_mapping_full_from_materialized(self):
        row_mapping_inverse = {v:k for (k,v) in self.row_mapping.items()}
        return row_mapping_inverse


    def len_full_data(self):
        """
        Returns the full length of the dataset. Not all this data might be initialized.
        This length can be unknown, if the full data set has not yet been derived.
        This length can also be infinite, in case an infinite generator is used to create
        this lazy table.
        """
        length = self.widget_origin.pull_length()
        #print("in len_full_data!", length)
        return length

    def len_instantiated_data(self):
        """
        Returns the length of the instantiated data. This is the data that is directly
        available to the widgets. The rest of the data can still be requested by accessing
        it though.
        """
        length = len(self.X)
        #print("in len_instantiated_data!", length)
        return length

    #take_len_of_instantiated_data = False
    take_len_of_instantiated_data = True
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


    #def append(self, *args, **kwargs):
    #    return self.fake_len(super().append, *args, **kwargs)

    #def insert(self, *args, **kwargs):
    #    return self.fake_len(super().insert, *args, **kwargs)


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


    def DISABLED_compute_basic_stats(self, include_metas=None):
        """
        _compute_basic_stats should return stats based on the full table,
        irrespective of what is currently materialized. It can only do this
        by pulling these statistics. There is no functionality to do that
        at the moment. Therefore this function provides some fake statistics.
        However, since the lazy widgets should never send an entirely empty
        table it should be possible to get decent statistics from the few
        materialized rows, making this overloading superfluous.

        _compute_basic_stats is faked.
        
        Returns a 6-element tuple or an array of shape (len(x), 6)
                Computed (min, max, mean, 0, #nans and #non-nans)
            
        TODO: Pull these statistics.
        """
        stats = [ (-9000, 9000, 0.0, 0, 0, len(self)) ] * len(self.domain)
        return stats
        
        
        
