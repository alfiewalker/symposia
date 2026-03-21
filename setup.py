"""
Setup script for Symposia - AI Committee Deliberation Framework
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Symposia - AI Committee Deliberation Framework"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="symposia",
    version="0.1.1",
    description="Deterministic committee-style validation library",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Symposia Team",
    author_email="team@symposia.ai",
    url="https://github.com/symposia/symposia",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "jsonschema>=4.0.0",
        ],
    },
    entry_points={
        'console_scripts': [
            'symposia=symposia.terminal.cli:entrypoint',
        ],
    },
    package_data={
        "symposia": [
            "profile_sets/stable/*.yaml",
            "profile_sets/registry/*.yaml",
            "profile_sets/experimental/*.yaml",
            "routing/*.yaml",
        ]
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai, llm, committee, deliberation, consensus, voting",
    project_urls={
        "Bug Reports": "https://github.com/symposia/symposia/issues",
        "Source": "https://github.com/symposia/symposia",
        "Documentation": "https://github.com/symposia/symposia/docs",
    },
) 