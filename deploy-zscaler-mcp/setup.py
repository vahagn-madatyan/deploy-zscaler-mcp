"""Setup script for deploy-zscaler-mcp."""

from setuptools import setup, find_packages

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="deploy-zscaler-mcp",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="CLI tool for deploying Zscaler MCP servers with AI assistants",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/deploy-zscaler-mcp",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "fastmcp>=2.5.1",
        "boto3>=1.34.0",
        "python-dotenv>=1.0.0",
        "tenacity>=8.2.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "deploy-zscaler-mcp=deploy_zscaler_mcp.__main__:main",
        ],
    },
)