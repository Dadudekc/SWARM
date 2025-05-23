"""
Setup script for Dream.OS package.
"""

from setuptools import setup, find_packages
import os

setup(
    name="dreamos",
    version="0.1.0",
    packages=find_packages(include=['dreamos', 'dreamos.*', 'agent_tools', 'agent_tools.*']),
    install_requires=[
        "pyautogui",
        "pyperclip",
        "Pillow",
        "pygetwindow",
        "schedule",
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "discord.py>=2.0.0",
        "python-dotenv>=0.19.0",
    ],
    package_data={
        "dreamos": ["core/*"],
        "agent_tools": ["utils/*"],
    },
    entry_points={
        'console_scripts': [
            'dreamos-menu=run_menu:main',
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