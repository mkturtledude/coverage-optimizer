# coverage-optimizer

## Installation
This project uses the following non-standard packages:
1. pandas
2. unidecode
3. pyscipopt
4. tkinter

The recommended way to install them is to create a conda environment:
```
conda create --name coverage-optimizer python=3.6 pandas
conda install --channel conda-forge pyscipopt unidecode
```

Then, to run the script:
```
conda activate coverage-optimizer
python src/gui.py
```

If you're interested in creating a stand-alone executable, add the following:
```
conda install pyinstaller
```
With that, you can do
```
pyinstaller --onefile --windowed src/gui.py
```
which will create the executable in the `dist` directory.

