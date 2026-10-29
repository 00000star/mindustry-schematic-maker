from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mindustry-schematic-maker",
    version="1.0.0",
    author="00000star",
    author_email="starboy@users.noreply.github.com",
    description="Automated closed-loop schematic generator, 3-tier static validator, and pure-Python supply simulator for Mindustry v7 Serpulo with zero dependencies.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/00000star/mindustry-schematic-maker",
    project_urls={
        "Bug Tracker": "https://github.com/00000star/mindustry-schematic-maker/issues",
        "Source Code": "https://github.com/00000star/mindustry-schematic-maker",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment :: Simulation",
        "Environment :: Console",
    ],
    packages=["core"],
    py_modules=["msch"],
    scripts=["msch"],
    entry_points={
        "console_scripts": [
            "msch = msch:main",
        ],
    },
    python_requires=">=3.8",
    install_requires=[],
)
