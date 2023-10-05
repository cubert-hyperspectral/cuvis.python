![image](https://camo.githubusercontent.com/9fc396a08b84779ea0f78a4085e96bee6035fca702cd382f38cb661fa1ff1d0c/68747470733a2f2f7777772e7370656374726f6578706f2e636f6d2f77702d636f6e74656e742f75706c6f6164732f323031382f30372f637562657274323031382e706e67)


# cuvis.python

cuvis.python is the python wrapper for the Cuvis SDK written in C ([available here](https://github.com/cubert-hyperspectral/cuvis.sdk)).

- **Website:** https://www.cubert-hyperspectral.com/
- **Source code:** https://github.com/cubert-hyperspectral/
- **Support:** http://support.cubert-hyperspectral.com/

This wrapper enables operating Cubert GmbH Hyperspectral Cameras, as well as, 
analyzing data directly from the corporate data format(s) within python.
This wrapper provides an object-oriented full representation of the basic C SDK 
capabilities and python return variable formats based on commonly used modules, 
like dictionaries, datetime or numpy objects.

For other supported program languages, please have a look at the 
source code page.

## Installation

### Prerequisites

First, you need to install the Cuvis C SDK from [here](https://cloud.cubert-gmbh.de/index.php/s/62UdmciCPjxy1pm).
The installation registers the installation path in the environment, which 
the python wrapper is linked to.

:warning: **If the C SDK is reinstalled into another directory later on, the 
linkage breaks and the python wrapper might stop working.**

### Via pip

If you wish to use cuvis within another project, from within your 
project environment, run 

```
pip install cuvis
```

or add `cuvis` to your project `requirements.txt` or `setup.py`.

### Via repository

If you wish to download and use cuvis locally, clone the git repository

  ```shell
  git clone git@github.com:cubert-hyperspectral/cuvis.python.git
  ```

and install the wrapper locally. 

For building the python bindings refer to [cuvis.pyil](https://github.com/cubert-hyperspectral/cuvis.pyil).

## How to ...

### Getting started

We provide an additional example repository [here](https://github.com/cubert-hyperspectral/cuvis.python.examples),
covering some basic applications.

Further, we provide a set of example measurements to explore [here](https://cloud.cubert-gmbh.de/index.php/s/3oECVGWpC1NpNqC).
These measurements are also used by the examples mentioned above.

### Getting involved

cuvis.hub welcomes your enthusiasm and expertise!

With providing our SDK wrappers on GitHub, we aim for a community-driven open 
source application development by a diverse group of contributors.
Cubert GmbH aims for creating an open, inclusive, and positive community.
Feel free to branch/fork this repository for later merge requests, open 
issues or point us to your application specific projects.
Contact us, if you want your open source project to be included and shared 
on this hub; either if you search for direct support, collaborators or any 
other input or simply want your project being used by this community.
We ourselves try to expand the code base with further more specific 
applications using our wrappers to provide starting points for research 
projects, embedders or other users.

### Getting help

Directly code related issues can be posted here on the GitHub page, other, more 
general and application related issues should be directed to the 
aforementioned Cubert GmbH [support page](http://support.cubert-hyperspectral.com/).

