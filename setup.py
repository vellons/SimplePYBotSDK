from setuptools import setup
from simplepybotsdk import __version__ as version

setup(
    name='simplepybotsdk',
    version=version,
    packages=['simplepybotsdk'],
    install_requires=['pyramid==1.10.5', 'websockets==8.1'],
    python_requires='>=3.5',
)
