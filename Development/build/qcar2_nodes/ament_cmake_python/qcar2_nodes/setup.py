from setuptools import find_packages
from setuptools import setup

setup(
    name='qcar2_nodes',
    version='0.0.0',
    packages=find_packages(
        include=('qcar2_nodes', 'qcar2_nodes.*')),
)
