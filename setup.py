from setuptools import setup

conf_file = open("./simplepybotsdk/configurations.py", "r")
version = conf_file.readline().split("\"")[1]
conf_file.close()
print("Building SimplePyBotSDK version {}".format(version))

setup(
    name='simplepybotsdk',
    version=version,
    packages=['simplepybotsdk'],
    install_requires=['pyramid==1.10.5', 'SimpleWebSocketServer==0.1.1'],
    python_requires='>=3.5',
)
