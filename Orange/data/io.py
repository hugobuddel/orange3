import csv
import re
import sys
import os
from collections import namedtuple

import bottleneck as bn
import numpy as np
from scipy import sparse

from ..data import _io
from ..data import Domain
from ..data.variable import *


class FileReader:
    def prescan_file(self, f, delim, nvars, disc_cols, cont_cols):
        values = [set() for _ in range(nvars)]
        decimals = [-1] * nvars
        for lne in f:
            lne = lne.split(delim)
            for vs, col in zip(values, disc_cols):
                vs[col].add(lne[col])
            for col in cont_cols:
                val = lne[col]
                if not col in Variable.DefaultUnknownStr and "." in val:
                    decs = len(val) - val.find(".") - 1
                    if decs > decimals[col]:
                        decimals[col] = decs
        return values, decimals


class TabDelimReader:
    non_escaped_spaces = re.compile(r"(?<!\\) +")

    def read_header(self, f):
        f.seek(0)
        names = f.readline().strip("\n\r").split("\t")
        types = f.readline().strip("\n\r").split("\t")
        flags = f.readline().strip("\n\r").split("\t")
        self.n_columns = len(names)
        if len(types) != self.n_columns:
            raise ValueError("File contains %i variable names and %i types" %
                             (len(names), len(types)))
        if len(flags) > self.n_columns:
            raise ValueError("There are more flags than variables")
        else:
            flags += [""] * self.n_columns

        attributes = []
        class_vars = []
        metas = []

        self.attribute_columns = []
        self.classvar_columns = []
        self.meta_columns = []
        self.weight_column = -1
        self.basket_column = -1

        for col, (name, tpe, flag) in enumerate(zip(names, types, flags)):
            tpe = tpe.strip()
            flag = flag.split()
            if "i" in flag or "ignore" in flag:
                continue
            if "b" in flag or "basket" in flag:
                self.basket_column = col
                continue
            is_class = "class" in flag
            is_meta = "m" in flag or "meta" in flag or tpe in ["s", "string"]
            is_weight = "w" in flag or "weight" in flag \
                or tpe in ["w", "weight"]

            if is_weight:
                if is_class:
                    raise ValueError("Variable {} (column {}) is marked as "
                                     "class and weight".format(name, col))
                self.weight_column = col
                continue

            if tpe in ["c", "continuous"]:
                var = ContinuousVariable.make(name)
            elif tpe in ["w", "weight"]:
                var = None
            elif tpe in ["d", "discrete"]:
                var = DiscreteVariable.make(name)
            elif tpe in ["s", "string"]:
                var = StringVariable.make(name)
            else:
                values = [v.replace("\\ ", " ")
                          for v in self.non_escaped_spaces.split(tpe)]
                var = DiscreteVariable.make(name, values, True)
            var.fix_order = (isinstance(var, DiscreteVariable)
                             and not var.values)

            if is_class:
                if is_meta:
                    raise ValueError(
                        "Variable {} (column {}) is marked as "
                        "class and meta attribute".format(name, col))
                class_vars.append(var)
                self.classvar_columns.append((col, var.val_from_str_add))
            elif is_meta:
                metas.append(var)
                self.meta_columns.append((col, var.val_from_str_add))
            else:
                attributes.append(var)
                self.attribute_columns.append((col, var.val_from_str_add))

        domain = Domain(attributes, class_vars, metas)
        return domain

    def count_lines(self, file):
        file.seek(0)
        i = -3
        for _ in file:
            i += 1
        return i

    def read_data(self, f, table):
        X, Y = table.X, table.Y
        W = table.W if table.W.shape[-1] else None
        f.seek(0)
        f.readline()
        f.readline()
        f.readline()
        padding = [""] * self.n_columns
        if self.basket_column >= 0:
            # TODO how many columns?!
            table._Xsparse = sparse.lil_matrix(len(X), 100)
        table.metas = metas = (
            np.empty((len(X), len(self.meta_columns)), dtype=object))
        line_count = 0
        Xr = None
        for lne in f:
            values = lne.strip()
            if not values:
                continue
            values = values.split("\t")
            if len(values) > self.n_columns:
                raise ValueError("Too many columns in line {}".
                                 format(4 + line_count))
            elif len(values) < self.n_columns:
                values += padding
            if self.attribute_columns:
                Xr = X[line_count]
                for i, (col, reader) in enumerate(self.attribute_columns):
                    Xr[i] = reader(values[col].strip())
            for i, (col, reader) in enumerate(self.classvar_columns):
                Y[line_count, i] = reader(values[col].strip())
            if W is not None:
                W[line_count] = float(values[self.weight_column])
            for i, (col, reader) in enumerate(self.meta_columns):
                metas[line_count, i] = reader(values[col].strip())
            line_count += 1
        if line_count != len(X):
            del Xr, X, Y, W, metas
            table.X.resize(line_count, len(table.domain.attributes))
            table.Y.resize(line_count, len(table.domain.class_vars))
            if table.W.ndim == 1:
                table.W.resize(line_count)
            else:
                table.W.resize((line_count, 0))
            table.metas.resize((line_count, len(self.meta_columns)))
        table.n_rows = line_count

    def reorder_values_array(self, arr, variables):
        for col, var in enumerate(variables):
            if var.fix_order and len(var.values) < 1000:
                new_order = var.ordered_values(var.values)
                if new_order == var.values:
                    continue
                arr[:, col] += 1000
                for i, val in enumerate(var.values):
                    bn.replace(arr[:, col], 1000 + i, new_order.index(val))
                var.values = new_order
            delattr(var, "fix_order")

    def reorder_values(self, table):
        self.reorder_values_array(table.X, table.domain.attributes)
        self.reorder_values_array(table.Y, table.domain.class_vars)

    def read_file(self, filename, cls=None):
        with open(filename) as file:
            return self._read_file(file, cls)

    def _read_file(self, file, cls=None):
        from ..data import Table
        if cls is None:
            cls = Table
        domain = self.read_header(file)
        nExamples = self.count_lines(file)
        table = cls.from_domain(domain, nExamples, self.weight_column >= 0)
        self.read_data(file, table)
        self.reorder_values(table)
        return table


class BasketReader():
    def read_file(self, filename, cls=None):
        if cls is None:
            from ..data import Table as cls
        def constr_vars(inds):
            if inds:
                return [ContinuousVariable(x.decode("utf-8")) for _, x in
                        sorted((ind, name) for name, ind in inds.items())]

        X, Y, metas, attr_indices, class_indices, meta_indices = \
            _io.sparse_read_float(filename.encode(sys.getdefaultencoding()))

        attrs = constr_vars(attr_indices)
        classes = constr_vars(class_indices)
        meta_attrs = constr_vars(meta_indices)
        domain = Domain(attrs, classes, meta_attrs)
        return cls.from_numpy(domain,
                              attrs and X, classes and Y, metas and meta_attrs)


class FixedWidthReader(TabDelimReader):
    """
    FixedWidthReader reads tables from files where the columns have a
    fixed width. The cells are space-padded to the left.
    See datasets/glass.fixed and tests/test_fixedwidth_reader.py
    
    It is possible to determine the exact cell location of a specific
    table cell within the file because of the fixed width columns.
    This allows the FixedWidthReader to be used with the LazyFile
    widget to 'read' extremely large files.
    
    TODO:
    - Add read_row() without reading entire file.
    - Allow spaces in column names and cell values.
    - Ensure compatibility with all tables in the tests directory.
    - Do metas and class properly.
    """

    def read_ends_columns(self, filename):
        """
        Returns the location where each column ends in a line in the
        file.

        TODO:
        - Cleanup.
        """
        ColumnInfo = namedtuple(
            'ColumnInfo',
            ['name', 'tpe', 'flag', 'start', 'end', 'width', 'index'],
        )
        with open(filename) as f:
            f.seek(0)
            l_names = f.readline()
            l_types = f.readline()
            l_flags = f.readline()
            types = l_types.split()
            ends = []
            for n in types:
                position_start = ends[-1] if len(ends) else 0
                end = (" "+l_types.replace("\n"," ")).find(" "+n+" ", position_start) + len(n)
                ends.append(end)
            info_columns = [
                ColumnInfo(
                    name=l_names[start:end].strip(),
                    flag=l_flags[start:end].strip(),
                    tpe=tpe,
                    start=start,
                    end=end,
                    width=end-start,
                    index=inde,
                ) for (inde, (start, end, tpe)) in enumerate(zip(
                    [0] + ends[:-1],
                    ends,
                    types,
                ))
            ]
            return info_columns

    

    def read_header(self, filename):
        """
        Reads the header of the fixed width file and returns the
        Domain of the table.
        
        TODO:
        - Use read_ends_columns() to determine the width of the
          columns and use that to parse the lines, because this
          will allow the use of spaces in column names.
        """
        ends = self.read_ends_columns(filename)
        names = [end.name for end in ends]
        types = [end.tpe for end in ends]
        flags = [end.flag for end in ends]
        with open(filename) as f:
            # Function based on read_header from TabDelimReader.
            f.seek(0)
            #names = f.readline().strip("\n\r").split()
            #types = f.readline().strip("\n\r").split()
            #flags = f.readline().strip("\n\r").split()
            f.readline()
            f.readline()
            f.readline()
            # Changed split on "\t" to split on spaces.
            self.n_columns = len(names)
            if len(types) != self.n_columns:
                raise ValueError("File contains %i variable names and %i types" %
                                 (len(names), len(types)))
            if len(flags) > self.n_columns:
                raise ValueError("There are more flags than variables")
            else:
                flags += [""] * self.n_columns

            attributes = []
            class_vars = []
            metas = []

            self.attribute_columns = []
            self.classvar_columns = []
            self.meta_columns = []
            self.weight_column = -1
            self.basket_column = -1

            for col, (name, tpe, flag) in enumerate(zip(names, types, flags)):
                tpe = tpe.strip()
                flag = flag.split()
                if "i" in flag or "ignore" in flag:
                    continue
                if "b" in flag or "basket" in flag:
                    self.basket_column = col
                    continue
                is_class = "class" in flag
                is_meta = "m" in flag or "meta" in flag or tpe in ["s", "string"]
                is_weight = "w" in flag or "weight" in flag \
                    or tpe in ["w", "weight"]

                if is_weight:
                    if is_class:
                        raise ValueError("Variable {} (column {}) is marked as "
                                         "class and weight".format(name, col))
                    self.weight_column = col
                    continue

                if tpe in ["c", "continuous"]:
                    var = ContinuousVariable.make(name)
                elif tpe in ["w", "weight"]:
                    var = None
                elif tpe in ["d", "discrete"]:
                    var = DiscreteVariable.make(name)
                elif tpe in ["s", "string"]:
                    var = StringVariable.make(name)
                else:
                    values = [v.replace("\\ ", " ")
                              for v in self.non_escaped_spaces.split(tpe)]
                    var = DiscreteVariable.make(name, values, True)
                var.fix_order = (isinstance(var, DiscreteVariable)
                                 and not var.values)

                if is_class:
                    if is_meta:
                        raise ValueError(
                            "Variable {} (column {}) is marked as "
                            "class and meta attribute".format(name, col))
                    class_vars.append(var)
                    self.classvar_columns.append((col, var.val_from_str_add))
                elif is_meta:
                    metas.append(var)
                    self.meta_columns.append((col, var.val_from_str_add))
                else:
                    attributes.append(var)
                    self.attribute_columns.append((col, var.val_from_str_add))

            domain = Domain(attributes, class_vars, metas)
            return domain

    def count_lines(self, filename):
        """
        Counts the number of lines in the file. This can be done
        without reading the entire file because the file
        has fixed width columns.
        """
        len_file = os.stat(filename).st_size
        with open(filename) as f:
            f.seek(0)
            line = f.readline()
            len_line = len(line)
        
        count = int(len_file / len_line) - 3
        return count

    def read_cell(self, filename, index_row, name_attribute):
        """
        Reads one specific cell value without reading the entire file.
        
        TODO:
        - Cleanup this function.
        - Test with discrete and class attributes.
        - Cache the header information.
        """
        info_columns = self.read_ends_columns(filename)
        header = self.read_header(filename)
        with open(filename) as f:
            f.seek(0)
            line = f.readline()
            len_line1 = len(line)

        len_line = sum(ic.width for ic in info_columns) + 1 # for \n
        col = [ic for ic in info_columns if ic.name == name_attribute][0]
        with open(filename) as f:
            f.seek( (3+index_row) * len_line + col.start )
            value = f.read(col.width)
            value_n = None
            # Parse the string in the correct format. This is a kludge
            # based on code from read_data().
            if self.attribute_columns:
                for i, (coli, reader) in enumerate(self.attribute_columns):
                    if coli == col.index:
                        value_n = reader(value.strip())
            for i, (coli, reader) in enumerate(self.classvar_columns):
                if coli == col.index:
                    value_n = reader(value.strip())

            return value_n
        

    def read_data(self, filename, table):
        """
        Read the data portion of the file.
        
        This function is based on the one in TabDelimReader.
        TODO:
        - Use the actual known width of the columns instead
          of splitting on space, because that will allow spaces
          to be part of the cell values.
          That is, use read_ends_columns.
        """        
        with open(filename) as f:
            X, Y = table.X, table.Y
            W = table.W if table.W.shape[-1] else None
            f.seek(0)
            f.readline()
            f.readline()
            f.readline()
            padding = [""] * self.n_columns
            if self.basket_column >= 0:
                # TODO how many columns?!
                table._Xsparse = sparse.lil_matrix(len(X), 100)
            table.metas = metas = (
                np.empty((len(X), len(self.meta_columns)), dtype=object))
            line_count = 0
            Xr = None
            for lne in f:
                values = lne.strip()
                if not values:
                    continue
                # Only difference with TabDelimReader
                #values = values.split("\t")
                values = values.split()
                if len(values) > self.n_columns:
                    raise ValueError("Too many columns in line {}".
                                     format(4 + line_count))
                elif len(values) < self.n_columns:
                    values += padding
                if self.attribute_columns:
                    Xr = X[line_count]
                    for i, (col, reader) in enumerate(self.attribute_columns):
                        Xr[i] = reader(values[col].strip())
                for i, (col, reader) in enumerate(self.classvar_columns):
                    Y[line_count, i] = reader(values[col].strip())
                if W is not None:
                    W[line_count] = float(values[self.weight_column])
                for i, (col, reader) in enumerate(self.meta_columns):
                    metas[line_count, i] = reader(values[col].strip())
                line_count += 1
            if line_count != len(X):
                del Xr, X, Y, W, metas
                table.X.resize(line_count, len(table.domain.attributes))
                table.Y.resize(line_count, len(table.domain.class_vars))
                if table.W.ndim == 1:
                    table.W.resize(line_count)
                else:
                    table.W.resize((line_count, 0))
                table.metas.resize((line_count, len(self.meta_columns)))
            table.n_rows = line_count

    def read_file(self, filename, cls=None):
        """
        Read a file.
        
        The distinction between read_file and _read_file cannot
        be made because we cannot get the length of a stream etc.
        """
        from ..data import Table
        if cls is None:
            cls = Table
        domain = self.read_header(filename)
        nExamples = self.count_lines(filename)
        table = cls.from_domain(domain, nExamples, self.weight_column >= 0)
        self.read_data(filename, table)
        self.reorder_values(table)
        return table
    

def csvSaver(filename, data, delimiter='\t'):
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=delimiter)
        writer.writerow([d.name for d in data.domain]) # write attribute names
        if delimiter == '\t':
            flags = ['']*len(data.domain)
            class_var = data.domain.class_var
            metas = data.domain.metas
            if class_var:
                flags[data.domain.indices[class_var.name]] = 'class'
            if metas:
                for m in metas:
                    flags[data.domain.indices[m.name]] = 'm'
            writer.writerow([str(d.var_type).lower() for d in data.domain]) # write attribute types
            writer.writerow(flags) # write flags
        for ex in data: # write examples
            writer.writerow(ex)

def saveCsv(filename, data):
    csvSaver(filename, data, ',')

def saveTabDelimited(filename, data):
    csvSaver(filename, data)
