#!/usr/bin/env python3
"""
Setup script for LetmeQC package.

This allows installing the package in development mode with:
    pip install -e .
"""

from setuptools import setup, find_packages
import os

# Read version from pyproject.toml or __init__.py
version = "0.1.0"

# Read long description from README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="letmeqc",
    version=version,
    description="Quality Control Tool for COCO Format Annotations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="VinAI Team",
    author_email="contact@vinai.io",
    url="https://github.com/your-org/letmeqc",
    package_dir={"": "."},
    packages=find_packages(where="."),
    python_requires=">=3.10",
    install_requires=[
        "shapely>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=24.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "letmeqc=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
)
