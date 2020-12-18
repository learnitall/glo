import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="glo",
    version="0.1",
    author="Ryan Drew",
    author_email="rdrew@learnin.today",
    description="Grocery List Optimizer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/learnitall/glo",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
