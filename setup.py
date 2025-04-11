from setuptools import setup, find_packages

setup(
    name="migration-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "google-generativeai>=0.3.1"
    ],
    entry_points={
        "console_scripts": [
            "migration-agent=cli:main"
        ]
    },
    author="MigrationAgent Team",
    author_email="example@example.com",
    description="A Python-based agent that analyzes Java/Maven projects and provides migration recommendations",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/username/migration-agent",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 