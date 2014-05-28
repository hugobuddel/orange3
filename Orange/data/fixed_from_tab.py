"""
Creates a fixed width column table from a tab separated table.
Fixed column width tables are used by the LazyFile widget because
it allows the widget to determine exactly where a given value is
in the file without having to read the entire file.
"""

import sys

def usage():
    """
    Print usage information and quit.
    """
    text_help = """Creates a fixed width column table from a tab separated table
Usage: {name} <tab-separated-filename> [fixed-width-filename]
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


def filename_fixed_from_filename_tab(filename_in):
    """
    Replace .tab with .fixed, e.g. "glass.tab" -> "glass.fixed".
    """
    filename_out = filename_in[:-4] + ".fixed" \
        if filename_in[-4:] == '.tab' \
        else filename_in + ".fixed"
    return filename_out

if __name__ == '__main__':
    if len(sys.argv) == 1:
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
