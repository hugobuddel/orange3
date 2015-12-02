wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda
# Useful for debugging any issues with conda
conda info -a

# Replace dep1 dep2 ... with your dependencies
conda create -q -n test-environment python=3.4 numpy scipy astropy sqlparse scikit-learn numpydoc beautifulsoup4 openpyxl sphinx setuptools pip wheel nose jinja2 numpydoc pyqt
source activate test-environment

#python setup.py install

# Disabled wheelhouse for the moment.
#if [ ! "$(ls wheelhouse)" ]; then
#    git clone -b pyqt --depth=1 https://github.com/astaric/orange3-requirements wheelhouse
#else
#    echo 'Using cached wheelhouse.';
#fi
#pip install wheelhouse/*.whl

pip install -r requirements.txt

python setup.py build_ext -i
