"""
A script to create a very large fixed width column file to test
the LazyFile widget.
"""


import urllib
import urllib.request
import astropy
import os
from astropy.io import fits

# See http://kids.strw.leidenuniv.nl/DR1/kids_dr1.0_src_wget.txt
url = "http://ds.astro.rug.astro-wise.org:8000/KiDS_DR1.0_129.0_-0.5_g_src.fits"
filename = url.split("/")[-1]
if not os.path.exists(filename):
    urllib.request.urlretrieve (url, filename)

hdulist = fits.open(filename)
tabledata = hdulist[1].data
print(tabledata[0])

columns = hdulist[1].columns
names_columns = [c.name for c in columns]
set(len(n) for n in names_columns)
{3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17}

headers = [
    "%20s"*len(names_columns) % tuple(names_columns),
    ("%20s" % ('c'))*len(names_columns),
    " "*20*len(names_columns)
]

#print headers

filename_out = filename.replace(".fits", ".fixed")
file_out = open(filename_out, 'w')
for h in headers:
    file_out.write(h+"\n")

for (i,d) in enumerate(tabledata):
    ds = "%20s"*len(names_columns) % tuple(d)
    file_out.write(ds + "\n")
    print(i,len(tabledata))


