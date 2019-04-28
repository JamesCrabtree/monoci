from os import path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

setup(
    name='monoci',

    version='1.0.0',

    # Author details
    author='James Crabtree',

    # Choose your license
    license='Proprietary',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',

        # Pick your license as you wish (should match "license" above)
        'License :: Other/Proprietary License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    packages=find_packages(),

    install_requires=[
        'gitpython        == 2.1.11',
        'docker           == 3.7.0',
        'pyyaml           == 5.1'
    ],

    extras_require={
        'dev': [
            'wheel'
        ]
    },

    entry_points={
        'console_scripts': [
            'mono-ci=monoci.mono_ci:main'
        ],
    },
)
