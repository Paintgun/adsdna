#!/usr/bin/env python3

from pathlib import Path

import setuptools

project_dir = Path(__file__).parent

setuptools.setup(
    name="pg-model-building",
    version="0.0.10",
    description="A Python project to build PG models",
    # Use UTF-8 encoding for README even on Windows by using the encoding argument.
    long_description=project_dir.joinpath("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    keywords=["python"],
    author="Paintgun LTD",
    url="https://github.com/Paintgun/pg-model-building",
    package_dir={"": "src"},
    python_requires=">=3.9, <4",
    install_requires=project_dir.joinpath("requirements.txt").read_text().split("\n"),
)
