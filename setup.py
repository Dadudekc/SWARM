"""
Setup script for Dream.OS package.
"""

from setuptools import setup, find_packages
import os

setup(
    name="dreamos",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dateutil",
        "typing-extensions",
        "PyQt5",
        "pytest",
        "pytest-cov",
        "black",
        "isort",
        "mypy",
        "jsonschema>=4.0.0",
        "aiofiles>=0.8.0",
        "pydantic>=2.0.0"
    ],
    package_data={
        "dreamos": ["utils/*"],
    },
    entry_points={
        'console_scripts': [
            'dreamos-menu=run_menu:main',
            "resume-agents = dreamos.cli.resume:main",
        ],
    },
    python_requires=">=3.8",
    author="Dream.OS Team",
    description="A distributed agent system for autonomous operations",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 
