#IDL/GDL kernel for Jupyter

Demo [Notebook](http://nbviewer.ipython.org/github/lstagner/idl_kernel/blob/master/demo.ipynb)

To install:
This requires the current development version of IPython 3.0-dev

```
sudo python setup.py install
```

This should make an IDL directory containing the kernelspec in the ~/.ipython/kernels directory. If the directory is not made then manually create the directory with the following commands.

```
mkdir ~/.ipython/kernels/IDL
cp kernelspec/kernel.json ~/.ipython/kernels/IDL
```

To run:
``` 
ipython console --kernel IDL 
```
or
```
ipython qtconsole --kernel IDL
```
or 
```
ipython notebook 
#Select kernel from dropdown menu
```


