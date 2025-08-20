#!/usr/bin/env python3
"""
Setup script for the AI Spreadsheet Interface (airtable-clone) project.
"""

from setuptools import setup, find_packages
import os

# Read the requirements from requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "AI Spreadsheet Interface - A Streamlit-based spreadsheet interface with Google Sheets and OpenAI integration"

setup(
    name="ai-spreadsheet-interface",
    version="0.1.0",
    description="A Streamlit-based spreadsheet interface that connects to Google Sheets and OpenAI's API",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Your Name",  # Update this with your actual name
    author_email="your.email@example.com",  # Update this with your actual email
    url="https://github.com/yourusername/airtable-clone",  # Update this with your actual repo URL
    packages=find_packages(),
    py_modules=[
        "app",
        "sheets_manager", 
        "ai_processor",
        "response_parser"
    ],
    install_requires=read_requirements(),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Streamlit",
    ],
    keywords="streamlit, google-sheets, openai, spreadsheet, ai",
    entry_points={
        "console_scripts": [
            "ai-spreadsheet=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.toml", "*.example"],
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/airtable-clone/issues",
        "Source": "https://github.com/yourusername/airtable-clone",
        "Documentation": "https://github.com/yourusername/airtable-clone#readme",
    },
)
