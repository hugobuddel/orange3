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

This version of Orange can read some astronomical dataformats and therefore
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

Starting Orange Canvas
----------------------

To start Orange Canvas from the command line, run:

    python3 -m Orange.canvas

Open the 'All Lazy Widgets' tutorial in 'Help' -> 'Tutorials' to see
most of the new features introduced in this fork.


