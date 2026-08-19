![image](https://raw.githubusercontent.com/cubert-hyperspectral/cuvis.sdk/main/branding/logo/banner.png)

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

>**Cuvis C SDK**\
>Download and install the lastest Cuvis C SDK.\
>Link: [Cuvis C SDK](https://cloud.cubert-gmbh.de/s/qpxkyWkycrmBK9m)

### Prerequisites

First, you need to install the Cuvis C SDK from [here](https://cloud.cubert-gmbh.de/s/qpxkyWkycrmBK9m).
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
We currently provide pre-compiled binaries for Python 3.9, 3.10, 3.11, 3.12, 3.13 and 3.14 for Windows, Ubuntu 20.04 and Ubuntu 22.04 (all 64-bit).

To access the newest python cuvis version (for use with SDK beta versions, etc) you can install it with

```
pip install cuvis --pre
```

### Via repository

If you wish to download and use the newest development cuvis locally, clone the git repository

  ```shell
  git clone git@github.com:cubert-hyperspectral/cuvis.python.git
  ```

and install the wrapper locally. 

If you wish to use the version compatible to the available Cuvis SDK download, check out the version on the site [above](https://cloud.cubert-gmbh.de/s/q3YiPZPJe5oXziZ) and use the respective release branch (e.g. [release/v3.2](https://github.com/cubert-hyperspectral/cuvis.python/tree/release/v3.2)).

For building the python bindings refer to [cuvis.pyil](https://github.com/cubert-hyperspectral/cuvis.pyil).

## Versioning

Wrapper versions are `MAJOR.MINOR.PATCH.TWEAK`.
`MAJOR.MINOR.PATCH` is the Cuvis C SDK release this wrapper targets, and `TWEAK` counts wrapper-only
revisions against that same SDK; `3.5.3.1` is a wrapper fix on top of `3.5.3.0`, both for SDK 3.5.3.

`main` always points at the latest released wrapper state, `develop` at the next release.
Every release is listed in [CHANGELOG.md](CHANGELOG.md).
The scheme and the release process are documented in [CONTRIBUTING.md](CONTRIBUTING.md).

## How to ...

### Getting started

We provide an additional example repository [here](https://github.com/cubert-hyperspectral/cuvis.python.examples),
covering some basic applications.

Further, we provide a set of example measurements to explore [here](https://cloud.cubert-gmbh.de/s/SrkSRja5FKGS2Tw).
These measurements are also used by the examples mentioned above.

### Configuring the SDK from code

The SDK reads its configuration from a `cuvis.settings` file in the directory passed to `cuvis.init()`.
`SdkSettings` lets you write that configuration in Python instead of maintaining the file by hand.

```python
import cuvis

settings = cuvis.SdkSettings(force_gpu_mode="cuda", processing_thread_count=8)
cuvis.init(settings)
```

It behaves like a dict, so you can inspect and edit it before applying it:

```python
settings["verbose"] = True          # booleans become "true" / "false"
del settings["force_gpu_mode"]
print(dict(settings))               # {'processing_thread_count': '8', 'verbose': 'true'}
print(settings.xml_str)             # the exact file that will be written
```

An existing configuration can be loaded from a settings file or from the directory containing one, and keyword arguments override what was loaded:

```python
settings = cuvis.SdkSettings("/path/to/settings_dir", processing_thread_count=4)
```

Used as a context manager it serializes itself into a temporary directory, which is useful for pointing other tools at the same configuration:

```python
with settings as settings_dir:
    cuvis.init(settings_dir)
```

Use `settings.save(path)` to write the file to a permanent location instead.

### Getting involved

cuvis.hub welcomes your enthusiasm and expertise!

With providing our SDK wrappers on GitHub, we aim for a community-driven open 
source application development by a diverse group of contributors.
Cubert GmbH aims for creating an open, inclusive, and positive community.
Feel free to branch/fork this repository for later merge requests, open 
issues or point us to your application specific projects.
Before opening a pull request, please read [CONTRIBUTING.md](CONTRIBUTING.md); it covers the branch 
model, the version scheme, the changelog conventions and the checks CI runs.
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

