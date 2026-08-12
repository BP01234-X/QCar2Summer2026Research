from setuptools import find_packages
from setuptools import setup

setup(
    name='qcar2_interfaces',
    version='0.0.0',
    packages=find_packages(
        include=('qcar2_interfaces', 'qcar2_interfaces.*')),
)
