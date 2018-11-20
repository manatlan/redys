import redys
import setuptools

setuptools.setup(
    name='redys',
    version=redys.__version__,

    author="manatlan",
    author_email="manatlan@gmail.com",
    description="A simple redis-like in pure python3, fully asyncio compliant",
    long_description=open("README.md","r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/manatlan/redys",
    py_modules=["redys"], #setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=[],
    keywords=['python3', 'redis', 'pickle', 'asyncio', 'queue', 'cache', 'set', "pubsub", "sync", "async"],
)
