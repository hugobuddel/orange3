"""
Creates a fixed width column table from a tab separated table.
Fixed column width tables are used by the LazyFile widget because
it allows the widget to determine exactly where a given value is
in the file without having to read the entire file.
"""

import sys
import os

def usage():
    """
    Print usage information and quit.
    """
    text_help = """Creates a fixed width column table from a tab separated table
Usage: {name} <tab-separated-filename> [fixed-width-filename]
  to convert any .tab file to a .fixed file.
Or: {name} glasslarge
  to create a large fixed-width version of the glass dataset.
The fixed-width files can be used with the LazyFile widget.
""".format(name = sys.argv[0])
    print(text_help)

def fixed_from_tab(filename_in, filename_out):
    """
    Create a fixed width column file from a tab separated column file.
    """
    with open(filename_in) as file_in:
        data = [l.strip("\n").split('\t') for l in file_in.readlines()]
    
    widths_columns = [
        max(len(c) for c in l)
        for l in zip(*data)
    ]
    
    data_fixed = [
        [
            "{value:>{width}}".format(value=cell, width=width)
            for (cell, width) in zip(line, widths_columns)
        ]
        for i,line in enumerate(data)
    ]
    
    data_string = "".join(
        " ".join(line) + "\n"
        for line in data_fixed
    )
    
    with open(filename_out, 'w') as file_out:
        file_out.write(data_string)

    print("Created {fout} from {fin}.".format(
        fout = filename_out,
        fin = filename_in
    ))


def create_glass_fixed_large():
    """
    Creat a large fixed-width version of the glass dataset.
    Run from Orange.datasets directory.
    """
    if not os.path.exists('glass.fixed'):
        if not os.path.exists('glass.tab'):
            print("Run in Orange.datasets directory.")
            return
        else:
            fixed_from_tab('glass.tab', 'glass.fixed')

    # And now for some real Pythonic code.
    ls1 = open('glass.fixed').readlines()
    h0 = "     "+ls1[0]
    h1 = "     "+ls1[1]
    h2 = "     "+ls1[2]
    d1 = ls1[3:]
    d2 = [l[3:] for l in d1]
    
    f = open('glasslarge.fixed', 'w')
    f.write(h0)
    f.write(h1)
    f.write(h2)
    c = 0
    for i in range(10000):
        for (j,l) in enumerate(d2):
            c += 1
            s = "%8i" % (c,) + l
            tt=f.write(s)

    f.close()
    print("Created glasslarge.fixed")

def create_glass_tab_large():
    """
    Creat a large tab-delimited version of the glass dataset.
    Run from Orange.datasets directory.
    """
    if not os.path.exists('glass.tab'):
        print("Run in Orange.datasets directory.")
        return

    # And now for some real Pythonic code.
    ls1 = open('glass.tab').readlines()
    h0 = ls1[0]
    h1 = ls1[1]
    h2 = ls1[2]
    d1 = ls1[3:]
    d2 = [l.split('\t')[1:] for l in d1]
    
    f = open('glasslarge.tab', 'w')
    f.write(h0)
    f.write(h1)
    f.write(h2)
    c = 0
    for i in range(10000):
        for (j,l) in enumerate(d2):
            c += 1
            s = "\t".join(["%i" % (c,)] + l)
            tt=f.write(s)

    f.close()
    print("Created glasslarge.tab")
            

def filename_fixed_from_filename_tab(filename_in):
    """
    Replace .tab with .fixed, e.g. "glass.tab" -> "glass.fixed".
    """
    filename_out = filename_in[:-4] + ".fixed" \
        if filename_in[-4:] == '.tab' \
        else filename_in + ".fixed"
    return filename_out

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'glasslarge':
        create_glass_tab_large()
        create_glass_fixed_large()
    elif len(sys.argv) == 1:
        usage()
    else:
        filename_in = sys.argv[1]
        filename_out = sys.argv[2] \
            if len(sys.argv) > 2 \
            else filename_fixed_from_filename_tab(filename_in)
        fixed_from_tab(
            filename_in,
            filename_out,
        )
