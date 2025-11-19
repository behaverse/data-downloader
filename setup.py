#!/usr/bin/env python3
"""
Setup script for Behaverse Data Manager

Professional Python package setup following standard conventions.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements from requirements.txt
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="behaverse-data-downloader",
    version="1.0.0",
    author="Behaverse",
    author_email="pedro@xcit.org",
    description="Python application for downloading and managing data from the Behaverse API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/behaverse/data-downloader",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "bdd=behaverse_data_downloader.cli:main",
        ],
    },
    include_package_data=True,
    keywords="data download api behaverse research downloader",
    project_urls={
        "Bug Reports": "https://github.com/behaverse/data-downloader/issues",
        "Source": "https://github.com/behaverse/data-downloader",
        "Documentation": "https://github.com/behaverse/data-downloader",
    },
)