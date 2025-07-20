# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 Zeus-Miner Project

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import re
import os
import codecs
import pathlib
from os import path
from io import open
from setuptools import setup, find_packages


def read_requirements(path):
    with open(path, "r") as f:
        requirements = f.read().splitlines()
        processed_requirements = []

        for req in requirements:
            # For git or other VCS links
            if req.startswith("git+") or "@" in req:
                pkg_name = re.search(r"(#egg=)([\w\-_]+)", req)
                if pkg_name:
                    processed_requirements.append(pkg_name.group(2))
                else:
                    # You may decide to raise an exception here,
                    # if you want to ensure every VCS link has an #egg=<package_name> at the end
                    continue
            else:
                processed_requirements.append(req)
        return processed_requirements


requirements = read_requirements("requirements.txt")
here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Loading version from template/__init__.py
with codecs.open(
    os.path.join(here, "template/__init__.py"), encoding="utf-8"
) as init_file:
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", init_file.read(), re.M
    )
    version_string = version_match.group(1) if version_match else "1.0.0"

setup(
    name="zeus_miner_subnet",
    version=version_string,
    description="Enhanced Bittensor subnet integrating Zeus ASIC hash work for top-ranking mining performance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Zeus-Miner Project",
    author_email="support@zeus-miner.com",
    url="https://github.com/Billoxinogen18/Zeus-Miner",
    packages=find_packages(exclude=("tests", "docs")),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "zeus-miner=neurons.miner:main",
            "zeus-validator=neurons.validator:main",
            "zeus-optimize=scripts.optimize_zeus:main",
            "zeus-monitor=scripts.monitor_performance:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/Billoxinogen18/Zeus-Miner/issues",
        "Source": "https://github.com/Billoxinogen18/Zeus-Miner",
        "Documentation": "https://github.com/Billoxinogen18/Zeus-Miner/blob/main/README.md",
    },
)
