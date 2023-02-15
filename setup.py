from setuptools import setup, find_packages

VERSION = '0.0.1'

with open("README.md") as f:
    readme = f.read()

setup(
    name="ezcord",
    version=VERSION,
    author="tibue99",
    license="MIT",
    description="An easy-to-use extension for the Pycord library",
    long_description_content_type="text/markdown",
    long_description=readme,
    packages=find_packages(),
    install_requires=["py-cord"],
    python_requires=">=3.8.0",
    keywords=['python', "discord", "py-cord", "pycord"],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)
