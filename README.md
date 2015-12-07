Orange
======

[![build: passing](https://img.shields.io/travis/hugobuddel/orange3.svg)](https://travis-ci.org/hugobuddel/orange3)
[![Coverage Status](https://coveralls.io/repos/hugobuddel/orange3/badge.svg?branch=master&service=github)](https://coveralls.io/github/hugobuddel/orange3?branch=master)
[![code quality: worse](https://img.shields.io/scrutinizer/g/hugobuddel/orange3.svg)](https://scrutinizer-ci.com/g/hugobuddel/orange3/)

Orange is a component-based data mining software. It includes a range of data
visualization, exploration, preprocessing and modeling techniques. It can be
used through a nice and intuitive user interface or, for more advanced users,
as a module for the Python programming language.

This is an adaptation of Orange 3 [orange3], adding request-driven data-pulling
features similar to lazy evaluation. Both Orange 3 and these adaptations
are in the early stages of development. This fork should therefore be
considered experimental.

[orange3]: https://github.com/biolab/orange3


Installing
----------

Install the following dependencies on debian based systems.

    sudo apt-get install libblas-dev liblapack-dev \
            postgresql-server-dev-9.1 libqt4-dev cvs \
            libbz2-dev libreadline6-dev zlib1g-dev \
            libfreetype6-dev libpng12-dev libaio-dev \
            libssl-dev python-openssl python-pysqlite2 \
            python-sqlite libsqlite3-dev python-tk \
            python-qt4-dev libqt4-dev libcfitsio3 \
            liberfa1 libwcs4 cython libxtst6 \

This version of Orange can read some astronomical data formats and therefore
requires astropy. Astropy and Python 3 can best be installed using anaconda.

    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p $HOME/miniconda
    export PATH="$HOME/miniconda/bin:$PATH"
    conda update conda
    conda install numpy scipy astropy sqlparse scikit-learn numpydoc \
        pip beautifulsoup4 openpyxl sphinx setuptools wheel nose \
        jinja2 numpydoc pyqt matplotlib -y

Then clone this repository (if not already done) and install Orange.

    git clone https://github.com/hugobuddel/orange3.git
    cd orange3
    pip install -r requirements.txt
    python setup.py develop

The LazyFile widget, described below, lets Orange handle very large
files. A demo file can be created by running

    pushd Orange/datasets
    python ../data/fixed_from_tab.py glasslarge
    popd

### Install Astro-WISE
Astro-WISE has to be installed in order to use the interoperability
features of this Orange fork. Astro-WISE can be installed as
follows:
    wget http://astro-wise.org/awesoft/awesetup
    chmod +x awesetup
    ./awesetup awehome=$HOME/awehome awetarget=astro versions=current pythonversion=2.7.9
and setting the appropriate path of the installation.



Starting Orange Canvas (and connecting to Astro-WISE)
-----------------------------------------------------

This Orange fork can communicate to other programs using the Simple
Application Message Protocol (SAMP). Start a SAMP hub before starting
Orange in order to use this functionality. E.g. with astropy installed
simply run

    start_hub

to start the astropy SAMP hub.

To start Orange Canvas from the command line, run:

    python3 -m Orange.canvas

Open the 'All Lazy Widgets' tutorial in 'Help' -> 'Tutorials' to see
most of the new features introduced in this fork.

This Orange fork allows Orange to pull data. That is, each widget can
request parts of the data it needs simply by accessing it. This can
even be done from an outside source. Currently only The Astro-WISE
information system is supported. Install Astro-WISE and start its
interactive shell with

    awe


Demos in the tutorial
---------------------

The 'All Lazy Widgets' tutorial shows all the new features. The
tutorial scheme can be found in the 'Tutorials' option of the 'Help'
menu.

### LazyFile & Data Table
The LazyFile widgets allows Orange to deal with arbitrarily sized
datasets in a file. An example dataset, `glasslarge.fixed` with
millions of rows can be created, see the installation instructions.
This is simply the glass dataset of the original Orange, concatenated
10000 times, stored in a new fixed-width file format.

Select the `glasslarge.fixed` dataset in the LazyFile widget and open
the Data Table widget. The info box of the Data Table widget shows
that the table contains 2140000 instances with 9 features. The table
can be browsed freely.

Only those instances that are actually shown on the screen will be
loaded into memory. This on-demand loading of data ensures that the
full table can be browsed, just like tables loaded with the original
File widgets, without running out of memory. Calling `print(in_data)`
in the Python Script widget shows how many instances have been
materialized; only a few hundred.


### InfiniTable & Scatter Plot
The new InfiniTable widget provides an arbitrarily large dataset.
The LazyTable and lazy widgets have been designed such that existing
widgets work unchanged.

The original Scatter Plot widget plots all the data of the incoming
Table by directly accessing numpy arrays in memory. It is (by design)
considered impossible to store all data of a LazyTable in memory.
Nevertheless, the LazyTable ensures that all data that is requested
by other widgets (e.g. the Data Table) is kept in memory. Furthermore,
a Lazy Table continuously requests some more data from the widget
that created it.

Therefore, the Scatter Plot will benefit from the living data approach
without adaptation. Firstly it will not be able to try to create a
visualization of all the instances, which would crash Orange. Secondly,
its visualization will continuously improve.

However, minimal changes have been applied to the Scatter Plot widget
to better benefit from the Lazy Table. In particular, the incoming
data is filtered using a Filter instance when the user zooms in
on a particular part of the graph. This allows the InfiniTable to
only create instances that are necessary for the visualization.


### SAMP and Stochastic Gradient Descent
This Orange fork can connect to the Astro-WISE information system.
First start the SAMP Hub, Orange, and Astro-WISE.

There are different experimental data pulling algorithms implemented
in Astro-WISE. The default depends on which Astro-WISE version is used;
the goal is to unify them in the future. Some work better with Orange
than others, and it is therefore necessary to ensure the right one
is used. To setup Astro-WISE for this demo, run the following in the
Astro-WISE command line:

    # Start the Samp client:
    samp = Samp()
    # Ensure that the incremental incremental data pulling
    # functionality is activated:
    samp.broadcast_sourcecollections_in_parts = True
    # Ensure that the experimental dependency graph generation is
    # disabled:
    samp.use_onthefly = False

Search (or pull) an interesting catalog (SourceCollection) in
Astro-WISE and share it with Orange. E.g.

    # Specify a SourceCollection to use
    universe = (SourceCollection.name == "demouniverseclassifystarsb").max('creation_date')
    samp.highlight_sourcecollection(universe)

No data is send over SAMP at this moment. Orange will immediately
request information about this catalog, e.g. which attributes its
instances have. It will subsequently request data for all attributes
for all sources. Astro-WISE will start sending data to Orange
in an incremental fashion. Adding a Data Table widget to the scheme
allows one to see this process.

This incremental retrieval of data can be seen by opening the
Stochastic Gradient Descent widget. The widget uses an iterator to
loop over the data it receives and will therefore automatically
improves its classification when more data arrives. That is, no
explicit code is used to 'request' more data, it simply accesses more
through the iterator.

The Stochastic Gradient Descent widget clearly shows that some parts
of the parameter space are easier to classify than others. Instances
in the 'difficult' contain more useful information than instances
in other regions, and the classifier could learn faster by training
on those difficult instances.

A region of interest can be selected automatically by checking the
'use region of interest' checkbox, or manually be dragging a
rectangular region on the shown scatter plot. The widget will
subsequently create a Filter object that selects only the informative
area in the parameter space. The Filter class in Orange is rather
passive, it asks the incoming data to apply the selection process
itself. The novel LazyTable class does not only select the proper
subset of instances, but also propagates this selection backwards.
The SAMP widget translates the region of interest from Orange'
internal Filter representation to the representation used by SAMP.
The widget subsequently sends a message to Astro-WISE which in turn
uses its own functionality to apply the filter to the data it sends
(and even creates if necessary).

Astro-WISE will subsequently start sending data in the region of
interest specified by the Stochastic Gradient Descent widget. Note
that in the current implementation it can take a while (about a minute)
for the entire system to 'catch up' to a new region of interest.
















