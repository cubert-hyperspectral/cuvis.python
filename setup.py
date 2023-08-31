import os
import platform
import sys
import io

from shutil import rmtree, copy
from setuptools import setup, find_packages, Command 
from setuptools.command import develop

here = os.path.abspath(os.path.dirname(__file__))

NAME = 'cuvis'
VERSION = '0.0.5'

def get_numpy_version():
	version = ''
	with open(os.path.join(here, 'cuvis.pyil', 'numpy_version.stamp')) as f:
		version = f.read()
	return version

def get_pyil_files():
    files = ['_cuvis_pyil.pyd', 'cuvis_il.py']
    with open(os.path.join(here, 'cuvis.pyil', 'binary_dir.stamp')) as f:
        path = f.read().strip('\n')

        for file in files:
            full_path = os.path.join(path, file)
            copy(full_path, os.path.join(here, 'cuvis'))
    pass

             

REQUIREMENTS = {
    # Installation script (this file) dependencies
    #'setup': [
    #    'setuptools_scm',
    #],
    # Installation dependencies
    # Use with pip install . to install from source
    'install': [
        str(f'numpy == {get_numpy_version()}'),
    ],
}

lib_dir = ""
if 'CUVIS' in os.environ:
    lib_dir = os.getenv('CUVIS')
    print('CUVIS SDK found at {}!'.format(lib_dir))
else:
    Exception(
        'CUVIS SDK does not seem to exist on this machine! Make sure that the environment variable CUVIS is set.')

# taken from https://github.com/navdeep-G/setup.py/blob/master/setup.py
class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Copying latest pyil files')
        get_pyil_files()

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('python setup.py sdist'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload -r testpypi dist/*')

        #self.status('Pushing git tags…')
        #os.system('git tag v{0}'.format(about['__version__']))
        #os.system('git push --tags')

        sys.exit()

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION


def __createManifest__(subdirs):
    """inventory all files in path and create a manifest file"""
    current = os.path.dirname(__file__)
    relative_paths = [os.path.relpath(path, current) for path in subdirs]

    single_files = [os.path.join(here, 'cuvis.pyil', 'numpy_version.stamp'),
                    os.path.join(here, 'DESCRIPTION.md')]

    rel_single_files = [os.path.relpath(path, current) for path in single_files]

    with open(os.path.join(current, "MANIFEST.in"), "w") as manifest:
        manifest.writelines(
            "recursive-include {} *.pyd \n".format(" ".join(relative_paths)))
        manifest.writelines(
            "recursive-include {} *.so \n".format(" ".join(relative_paths)))
        manifest.writelines(
            "include {}  \n".format(" ".join(rel_single_files)))


add_il = os.path.join(here, "cuvis")

__createManifest__([add_il])

# Import the DESCRIPTION.md and use it as the long-description.
# Note: this will only work if 'DESCRIPTION.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'DESCRIPTION.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION


setup(
    name=NAME,
    python_requires='>= 3.9',
    version=VERSION,
    packages=find_packages(),
    url='https://www.cubert-hyperspectral.com/',
    license='Apache License 2.0',
    author='Ben Mueller @ Cubert GmbH, Ulm, Germany',
    author_email='mueller@cubert-gmbh.com',
    description='CUVIS Python SDK.'
                ' Linked to the cuvis installation at {}.'.format(
        lib_dir),
    #setup_requires=REQUIREMENTS['setup'],
    install_requires=REQUIREMENTS['install'],
    include_package_data=True,
	cmdclass={
        'upload': UploadCommand,
    },
)
