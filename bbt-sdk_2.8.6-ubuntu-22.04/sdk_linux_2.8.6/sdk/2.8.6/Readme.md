# Readme
This is the SDK for interacting with Bitbrain devices

For more information take a look in the [documentation](https://cdn.bitbrain.com/sdk/c/2.8.6/index.html)

We provide an example in an [public repository](https://gitlab.com/bitbrain-public/sdk) to show how to use the SDK.

## Note about python support

Python SDK is no longer released with the C SDK.
This decission has been made to avoid dealing with multiple python versions and their compatibility problems.
Instead, we propose here different options to easily use this C SDK from python:
- [swig](https://www.swig.org/)
- [CFFI](https://cffi.readthedocs.io/en/stable/index.html)
- [ctypes](https://docs.python.org/3/library/ctypes.html)

Find [here](https://realpython.com/python-bindings-overview/) a very complete post about these and other options to access the SDK from python with their pros and cons. 
