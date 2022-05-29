# coverage-optimizer

## Installation
This project uses the following non-standard packages:
1. pandas
2. unidecode
3. pyscipopt
4. tkinter

The recommended way to install them is to use the Anaconda distribution. After installing it, go to the anaconda shell (Windows) or to a normal terminal (Mac & Linux) and create a conda environment:
```
conda create --name coverage-optimizer python=3.6 pandas
conda install --channel conda-forge pyscipopt unidecode
```

To run the script:
```
conda activate coverage-optimizer
python gui.py
```

If you're interested in creating a stand-alone executable, add the following:
```
conda install pyinstaller
```
With that, you can do
```
pyinstaller --onefile --windowed gui.py
```
which will create the executable in the `dist` directory.

Anaconda also provides a GUI which should allow to do all of this, but I only have experience with the command-line version.

