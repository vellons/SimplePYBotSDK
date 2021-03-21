from setuptools import setup
from simplepybotsdk import __version__ as version

setup(
    name='simplepybotsdk',
    version=version,
    packages=['simplepybotsdk'],
    install_requires=['pyramid==1.10.5', 'SimpleWebSocketServer==0.1.1'],
    python_requires='>=3.5',
)
