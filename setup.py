import os
import platform
import sys
import io
import subprocess
from shutil import rmtree, copy
from setuptools import setup, find_packages, Command
from setuptools.command import develop
from pathlib import Path

here = os.path.abspath(os.path.dirname(__file__))

NAME = 'cuvis'
VERSION = '3.3.2rc1'

DESCRIPTION = 'CUVIS Python SDK.'

REQUIREMENTS = {
    # Installation script (this file) dependencies
    # 'setup': [
    #    'setuptools_scm',
    # ],
    # Installation dependencies
    # Use with pip install . to install from source
    'install': [
        'cuvis-il>3.3.1,<=3.3.2.post999999',
    ],
}

lib_dir = ""
if 'CUVIS' in os.environ:
    lib_dir = os.getenv('CUVIS')
    print('CUVIS SDK found at {}!'.format(lib_dir))
else:
    Exception(
        'CUVIS SDK does not seem to exist on this machine! Make sure that the environment variable CUVIS is set.')


def get_git_commit_hash() -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except subprocess.CalledProcessError:
        return 'unknown'

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

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('python setup.py sdist'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        # self.status('Pushing git tags…')
        # os.system('git tag v{0}'.format(about['__version__']))
        # os.system('git push --tags')

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

    single_files = [os.path.join(here, 'README.md'),
                    os.path.join(here, 'git-hash.txt')]

    rel_single_files = [os.path.relpath(path, current)
                        for path in single_files]

    with open(os.path.join(current, "MANIFEST.in"), "w") as manifest:
        # manifest.writelines(
        #    "recursive-include {} *.pyd \n".format(" ".join(relative_paths)))
        # manifest.writelines(
        #    "recursive-include {} *.so \n".format(" ".join(relative_paths)))
        manifest.writelines(
            "include {}  \n".format(" ".join(rel_single_files)))


add_il = os.path.join(here, "cuvis")

__createManifest__([add_il])

# Import the README.md and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

with open(Path(__file__).parent / "git-hash.txt", 'w') as f:
    f.write(f'{get_git_commit_hash()}\n')

setup(
    name=NAME,
    python_requires='>= 3.9',
    version=VERSION,
    packages=find_packages(),
    url='https://www.cubert-hyperspectral.com/',
    license='Apache License 2.0',
    author='Cubert GmbH, Ulm, Germany',
    author_email='SDK@cubert-gmbh.com',
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    # setup_requires=REQUIREMENTS['setup'],
    install_requires=REQUIREMENTS['install'],
    include_package_data=True,
        cmdclass={
        'upload': UploadCommand,
    },
)
