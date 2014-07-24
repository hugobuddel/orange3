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

from Orange.data import (domain as orange_domain,
                         io, DiscreteVariable, ContinuousVariable)

import numpy
import threading
import copy

def len_data(data):
    """
    Returns the length of data.

    For normal Table instances this is simply len(data), which is the length
    of the table as loaded into memory. However, for LazyTables not all the
    data might be loaded into memory. Nonetheless, __len__() of a LazyTable
    has to return the actual number of rows stored in memory in order to
    allow the LazyTable to be used with all existing widgets. Smart widgets,
    like this one, can use the len_full_data() in order to get the length
    of the full dataset. They can subsequently ask for the data they need
    in order to get it instantiated.
    """
    length = data.len_full_data() if isinstance(data, LazyTable) else len(data)
    return length


class LazyRowInstance(RowInstance):
    """
    LazyRowInstance is a lazy version of RowInstance.
    
    This is a very early rudimentary version.
    """

    # There are four different identifiers in use for a LazyRowInstance:
    # - row_index_full:
    #   The number the row in the full conceptual table.
    #   This is a sequential integer starting at 0 and ending at
    #   self.table.len_full_data().
    #   The instances in identical LazyTables should always have identical
    #   row_index_full values.
    #   This index is (currently) used when widgets ask for a specific row,
    #   because 1) the widgets should not be aware of row_index_materialized
    #   and 2) the widgets cannot yet use row_index_global.
    # - row_index_materialized:
    #   The identifier of the row in table.X, table.Y and table.metas.
    #   This is also a sequential integer starting at 0 and ending at
    #   self.table.len_full_data(). However, the order depends on the order
    #   in which the rows are materialized and therefore does not have to be
    #   same as those of row_index_full.
    #   The instances of identical LazyTables could have different
    #   row_index_materialized values.
    #   This index should only be used internally, since its value is
    #   essentially meaningless outside self.table.
    # - instance_index_global:
    #   A unique identifier of the instance. Conceptually this is like a
    #   name or label of the instance and therefore does not have to be
    #   numerical.
    #   The same instance in several tables will have the same
    #   instance_index_global.
    #   This identifier cannot yet be used.
    # - row_index:
    #   For external use, that is, in __getitem__ of LazyTable, row_index is
    #   referring to row_index_full. This ensures that the interface between
    #   the widgets and LazyTable is the same as with the normal Table.
    #   For internal use, that is, in __getitem__ of LazyRowInstance, row_index
    #   is referring to row_index_materialized. This ensures that the Table,
    #   being the superclass of LazyTable, works as expected.
    #   Within the class, row_index_full or row_index_materialized should be
    #   used instead of row_index whenever possible for clarity.
    # For example when rows are removed from table.X, Y and metas because of
    # memory constraints, then the row_index_full of each row will stay the
    # same, but the row_index_materialized will change. Such functionality
    # has not yet been implemented.

    row_index_full = None
    row_index_materialized = None
    instance_index_global = None

    def __init__(self, table, row_index, region_of_interest_only=False):
        """
        Construct a data instance representing the given row of the table.
        row_index is the real row of the data set, which might not be the
        materialized row.

        When region_of_interest_only is set, then the row is only stored
        in the table if it's in the region_of_interest. It should only be
        necessary to set this flag internally.

        TODO:
        - Ensure that rows that are not in the region of interest are
          removed from memory because saving memory is the reason they are
          not appended to the table.
        - Perhaps cache whether an instance is in the region of interest
          so they can be skipped later.
        """

        # The table that this row belongs to, should be a LazyTable instance.
        self.table = table

        # row_index_full is enough to get the attribute values of this row.
        self.row_index_full = row_index

        # TODO: A None for row_index_materialized should not happen anymore
        #   because this is now checked in LazyTable.__getitem__(). However
        #   this does mean that the in_roi code is not functional anymore.
        #   Replace all the RoI code with Filters?
        # row_index_materialized is used to cache the attribute values in
        # memory in self.table.X, Y and metas. It is set to None if there is
        # no corresponding row in self.table.
        self.row_index_materialized = table.row_mapping.get(self.row_index_full, None)

        if self.row_index_materialized is None:
            # The row has not yet been stored in the table. We instantiate
            # Instance (super of RowInstance) instead of RowInstance because
            # there is no corresponding row in memory yet.
            Instance.__init__(self, table.domain)
            # Nevertheless, from this moment on, we can use this
            # LazyRowInstance because all attribute values can be retrieved
            # on the fly.
            if self.in_filters():
                # The row is new and within the filter.
                # Therefore needs to be added to
                # be appended to self.table. The new row_index_materialized
                # will be set to the current length of the table in memory.
                # This ensures that the row is inserted at the right place
                # (that is, at the end) when appending.
                self.row_index_materialized = table.len_instantiated_data()
                self.row_index = self.row_index_materialized
                self.table.append(self)
                self.table.row_mapping[self.row_index_full] = self.row_index_materialized
                # A full RowInstance can now be initialized because the row
                # is indeed available in the table.
                RowInstance.__init__(self, table, self.row_index_materialized)
            elif not region_of_interest_only or self.in_region_of_interest():
                # TODO: Replace this region_of_interest stuff with
                #   Filter stuff above. Right now this is not called
                #   anymore at all?
                # The row is new and either in the region of interest or
                # requested explicitly and therefore needs to be added to
                # be appended to self.table. The new row_index_materialized
                # will be set to the current length of the table in memory.
                # This ensures that the row is inserted at the right place
                # (that is, at the end) when appending.
                self.row_index_materialized = table.len_instantiated_data()
                self.row_index = self.row_index_materialized
                self.table.append(self)
                self.table.row_mapping[self.row_index_full] = self.row_index_materialized
                # A full RowInstance can now be initialized because the row
                # is indeed available in the table.
                RowInstance.__init__(self, table, self.row_index_materialized)
            else:
                # This new row is not available in the table, and we'd like
                # to keep it this way to conserve memory.
                self.row_index_materialized = None
                self.row_index = self.row_index_materialized
        else:
            # The row is already available in the table.
            RowInstance.__init__(self, table, self.row_index_materialized)


    def __getitem__(self, key):
        """
        Returns a specific value by asking the table
        for the value.
        
        TODO:
        - Add support for Y and metas.
        - Do the conversion to Value properly.
        - Pull from self.table instead of from self.table.widget_origin?
        """

        # Get the keyid to access self._values.
        if isinstance(key, str):
            keyid = [i for (i,k) in enumerate(self.table.domain) if k.name == key][0]
            key = self.table.domain.variables[keyid]
        elif isinstance(key, int):
            keyid = key
            key = self.table.domain[keyid]
        else:
            keyid = [i for (i,k) in enumerate(self.table.domain) if k == key][0]

        # Get the keyid_variables to access self.table.X.
        # TODO: Get the keyid_variables properly. There must be a better way
        #   to do this. E.g. what happens if class_var is not the last column?
        keyids_variables = [i for (i,k) in enumerate(self.table.domain.variables) if k == key]
        keyid_variables = keyids_variables[0] if len(keyids_variables) else None

        # Get the value cached in memory.
        value = self._values[keyid]

        # A nan means the value is not yet available.
        if numpy.isnan(value):
            # Pull and cache the value.
            # TODO: Pull from self.table.widget_origin?
            if self.table.widget_origin is not None:
                value = self.table.widget_origin.pull_cell(self.row_index_full, key)
            elif self.table.table_origin is not None:
                value = self.table.table_origin[self.row_index_full][key]

            # TODO: Is this necessary? Where does the 'int' come from?
            if isinstance(value, (int, numpy.float)):
                value = float(value)

            # Cache the value both in this RowInstance as well as in
            # the original table.
            # TODO: Can we do everything with only self.table.X?
            self._values[keyid] = value

            # Only cache in self.table if there is a corresponding row there.
            if self.row_index_materialized is not None:
                # TODO: Ensure Y and metas are supported.
                if keyid_variables is not None:
                    # TODO: This if-statement below is probably wrong.
                    if keyid_variables < self.table.X.shape[1]:
                        self.table.X[self.row_index_materialized][keyid_variables] = value
                    else:
                        # TODO: Fix this probably incorrect way of handling
                        #   class vars because now all class_vars have to be
                        #   at the end of hte domain, is this enforced?
                        self.table.Y[self.row_index_materialized][keyid_variables - self.table.X.shape[1]] = value


        # TODO: Convert to Value properly, see __getitem__ in Instance.
        val = Value(key, value)

        return val

    def __str__(self):
        # TODO: Do something sensible here!
        return "Some LazyRowInstance"

    def in_filters(self, filters=None):
        """
        Return True if this row is in the filters.
        """
        if filters is None:
            filters = self.table.row_filters

        in_filters = True
        for filter_ in filters:
            in_filters &= filter_(self)

        return in_filters

    def in_region_of_interest(self, region_of_interest=None):
        """
        Returns whether a given instance is in a region of interest.

        The region of interest is currently specified as a dictionary. Like
        region_of_interest = {
               'attribute_name_1': (minimum_value, maximum_value),
               'attribute_name_2': (minimum_value, maximum_value),
        }
        This will probably change in the future. E.g. it might be more general to
        use an SQL WHERE clause or perhaps use the Filter class.

        E.g., the region_of_interest can is specified as SQL WHERE clause like
        region_of_interest_in_sql = " AND ".join(
            ''' "%s" BETWEEN %f AND %f ''' % (
                name, values[0], values[1]
            ) for (name, values) in region_of_interest
        )

        TODO:
        - Add support for multiple regions of interest.
          What if there are multiple widgets, each with their own region
          of interest? Track regions_of_interest with some identifier?
          and remove the region of interest when the widget doesn't need it
          anymore?
        """
        # Try to get the region of interest from the data itself.
        if region_of_interest is None:
            region_of_interest = self.table.region_of_interest

        # By default there is no region of interest, which means that 'everything
        # is interesting'.
        if region_of_interest is None:
            return True

        in_region_parts = [
            minimum <= self[attribute_name] <= maximum
            for (attribute_name, (minimum, maximum)) in region_of_interest.items()
        ]
        in_region = all(in_region_parts)
        return in_region



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
    #
    # Data pulling (1) might better be implemented in another way. At the
    # moment, the LazyTable has to ask widget_origin for more data. It
    # might be better if widget_origin tells the LazyTable instance how
    # it should retrieve more data itself. That has two benefits:
    # - the LazyTable instance is more self-contained and
    # - it will be easier for widget_origin to have multiple outputs.
    #
    # TODO: Implement this 'teaching' of the LazyTable
    widget_origin = None

    # Or this LazyTable can be created from another LazyTable, by some
    # widget like SelectingData.
    table_origin = None

    # row_mapping is a dictionary that maps other identifiers to rows of
    # .X, .Y and .metas. This is necessary because the rows might be fetched
    # in non-sequential order. That is, if row 10 is requested first (e.g.
    # by table[10]), then the first row in X, Y and metas refers to row
    # 10 in the table.
    row_mapping = None

    # region_of_interest specifies what part of the dataset is interesting
    # according to widgets further in the scheme. See in_region_of_interest()
    # of LazyRowInstance for information about its structure.
    region_of_interest = None

    stop_pulling = False


    # TODO: this seems ugly, overloading __new__
    #def __new__(cls, *args, **kwargs):
    #    print("LazyTable __new__() %s" % (cls))
    #    self = super().__new__(cls, *args, **kwargs)
    #    # No rows to map yet.
    #    self.row_mapping = {}
    #    return self

    def __init__(self, *args, **kwargs):
        # No rows to map yet.
        self.row_mapping = {}

        if 'stop_pulling' in kwargs:
            self.stop_pulling = kwargs['stop_pulling']

        super().__init__(*args, **kwargs)

        self.row_filters = ()
        # row_filters is used like in SqlTable.

        self.widget_origin = kwargs.get('widget_origin', None)

        if not self.stop_pulling:
            self.pull_in_the_background()


    def __getitem__(self, index_row, region_of_interest_only=False):
        """
        Get a row of the table. index_row refers to index_row_full, the
        row identifier of the full dataset.

        When region_of_interest_only is set, then the row is only stored
        in the table if it's in the region_of_interest. It should only be
        necessary to set this flag internally.
        """
        if isinstance(index_row, int):
            row_index_full = index_row

            # TODO: The len_full_data() is not yet implemented for
            #   tables with .table_origin and this check should therefore
            #   not be implemented here!
            # This raise makes it possible to use the LazyTable as an
            # iterator, e.g. in Table.save().
            if index_row >= self.len_full_data():
                raise IndexError

            # Just a normal row.
            # row_index_materialized is used to cache the attribute values in
            # memory in self.table.X, Y and metas. It is set to None if there is
            # no corresponding row in self.table.
            row_index_materialized = self.row_mapping.get(row_index_full, None)
            if row_index_materialized is not None:
                # TODO: or row_index_materialized here?
                row = LazyRowInstance(self, row_index_full, region_of_interest_only=region_of_interest_only)
            elif self.widget_origin is not None:
                # Actually do the same thing, since the pulling logic is
                # currently implemented in LazyRowInstance.
                row = LazyRowInstance(self, row_index_full, region_of_interest_only=region_of_interest_only)
            elif self.table_origin is not None:
                # Go through the original table and see whether we find
                # a row that fits in the table.
                row_index_counter = 0
                # TODO: Start as far as possible into table_origin instead
                #   of at the beginning.
                for row_origin in self.table_origin:
                    if row_origin.in_filters(self.row_filters):
                        row_index_counter += 1
                        if row_index_counter > row_index_full:
                            # Found it!
                            #row = row_origin.copy()
                            row = row_origin
                            row.table = self
                            row_index_full_old = row.row_index_full
                            row.row_index_full = row_index_full
                            # TODO: The below is similar to LazyRowInstance.
                            #   __getitem__(), perhaps that code there should
                            #   go to here?
                            row.row_index_materialized = self.len_instantiated_data()
                            row.row_index = row.row_index_materialized
                            self.append(row)
                            self.row_mapping[row.row_index_full] = row.row_index_materialized
                            # A full RowInstance can now be initialized because the row
                            # is indeed available in the table.
                            row = LazyRowInstance(self, row.row_index_full, region_of_interest_only=region_of_interest_only)
                            break
                else:
                    # Went through all the rows in origin_table, no dice..
                    raise IndexError
            else:
                raise NotImplementedError

            if row.row_index_materialized is not None:
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

    def copy(self):
        # TODO: Docstring
        # TODO: Use from_domain properly, but how?
        # TODO: Allow both these cases in some way?:
        #   t2.table_origin = self
        #   t2.widget_origin = self.widget_origin
        t2 = LazyTable.from_domain(self.domain)
        t2.stop_pulling = self.stop_pulling
        t2.table_origin = self
        return t2

    def _filter_values(self, f):
        # TODO: Docstring.
        # Need to copy f because e.g. SelectData will negate it etc.
        f2 = copy.deepcopy(f)
        t2 = self.copy()
        t2.row_filters += (f2,)
        return t2


    def pull_region_of_interest(self):
        if self.widget_origin is not None:
            self.widget_origin.pull_region_of_interest()

    def pull_in_the_background(self):
        """
        Keep pulling data in the background.

        TODO:
        - Stop pulling when running out of memory. Perhaps start deleting rows
          that are not in the region of interest?
        - Continue to pull data outside the region_of_interest when we got
          all of that?

        """
        if not self.stop_pulling:
            self.pull_region_of_interest()
            threading.Timer(10, self.pull_in_the_background).start()



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

    def set_region_of_interest(self, region_of_interest):
        """
        A region of interest has been indicated, probably by the user.
        Propagate this information to the widget providing the data, so it
        can fetch more data for this region of interest.
        """
        self.region_of_interest = region_of_interest
        self.widget_origin.set_region_of_interest(region_of_interest)

    def len_full_data(self):
        """
        Returns the full length of the dataset. Not all this data might be initialized.
        This length can be unknown, if the full data set has not yet been derived.
        This length can also be infinite, in case an infinite generator is used to create
        this lazy table.
        """
        if self.widget_origin is not None:
            length = self.widget_origin.pull_length()
        elif self.table_origin is not None:
            # TODO: The below is incorrect. Either
            # - Iterate through all rows and get the result. This materializes
            #   the entire table.
            # - Calculate the len_full_data().
            # - Iterate through the full table without caching the result.
            #   Cannot be done for very large tables.
            # - Raise exception if not all rows have been instantiated yet.
            # - ??
            length = self.table_origin.len_full_data()

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
        if False:
            import inspect
            frame_current = inspect.currentframe()
            frame_calling = inspect.getouterframes(frame_current, 2)
            print("LazyTable __len__", frame_calling[1][1:4])
        
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

    def extend(self, instances):
        """
        Hack to concatenate LazyTables.
        """
        # TODO: Properly implement this, think about what it means for
        #   LazyTables to be extended.
        # TODO: What about rowmapping?
        # TODO: How to test domains for equality??
        old_length = self.len_instantiated_data()
        #assert isinstance(instances, LazyTable) and instances.domain == self.domain, "Extend only supported for LazyTables"
        assert isinstance(instances, LazyTable), "Extend only supported for LazyTables"
        new_length = old_length + instances.len_instantiated_data()
        self._resize_all(new_length )
        self.X[old_length:] = instances.X
        self.Y[old_length:] = instances.Y
        self.metas[old_length:] = instances.metas
        if self.W.shape[-1]:
            if instances.W.shape[-1]:
                self.W[old_length:] = instances.W
            else:
                self.W[old_length:] = 1

        # Hack for row_mapping so OWTable works with OWSAMP.
        # This destroys all other use of the LazyTable.
        self.row_mapping = {i: i for i in range(new_length)}


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

    # TODO: Figure out how to stop the pulling properly.
    def closeEvent(self, ev):
        self.stop_pulling = True
        super().closeEvent(ev)

    def __del__(self):
        self.stop_pulling = True
