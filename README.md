#IDL/GDL kernel for IPython/Jupyter

Demo [Notebook](http://nbviewer.ipython.org/github/lstagner/idl_kernel/blob/master/demo.ipynb)

To install:

This requires IPython >3.0 and Pexpect 3.3

```
python setup.py install --prefix=~/.local
```

This should make an IDL directory containing the kernelspec in the ~/.ipython/kernels directory.

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


