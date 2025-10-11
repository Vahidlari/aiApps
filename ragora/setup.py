from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="ragora",
    version="0.1.0",
    author="Vahid Lari",
    author_email="vahidlari@gmail.com",
    description="A RAG system for creating knowledge bases from LaTeX documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vahidlari/aiapps",
    packages=find_packages(include=["ragora*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Markup :: LaTeX",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ragora=ragora.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ragora": [
            "config/*.yaml",
            "config/*.yml",
            "examples/*.py",
            "examples/latex_samples/*.tex",
        ],
    },
)
