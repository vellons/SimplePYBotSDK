from setuptools import setup

setup(
    name='simplepybotsdk',
    version='0.3.beta2',
    packages=['simplepybotsdk'],
    install_requires=['pyramid==1.10.5', 'websockets==8.1'],
    python_requires='>=3.5',
    url='https://github.com/vellons/SimplePYBotSDK',
    license='',
    author='Vellons',
    description='A simple Python3 library to manage the states of servomotors and sensor in a robot.'
)
