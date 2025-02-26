from setuptools import setup, find_packages

# Package meta-data.
NAME = "sentinel"
DESCRIPTION = "LLM App-based security system"
URL = ""
AUTHOR = ""
PYTHON_REQUIRES = ">=3.12.0"
VERSION = "0.1.0"

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    python_requires=PYTHON_REQUIRES,
    URL=URL,
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        "pygments",
        "langchain",
        "langchain_community",
        "transformers",
        "tensorflow",
        "tf",
        "langchain_openai",
        "docker",
    ],
)
