#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os
import sys
from setuptools import setup
from pathlib import Path


name = "djangorestframework-serializer-extensions"
package = "rest_framework_serializer_extensions"
description = "Extensions to DRY up Django Rest Framework serializers"
url = "https://github.com/evenicoulddoit/django-rest-framework-serializer-extensions"
author = "Ian Clark"
author_email = "dev@ianclark.me"
license = "BSD"
long_description_content_type = "text/markdown"


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, "__init__.py")).read()
    return re.search(
        "^__version__ = ['\"]([^'\"]+)['\"]", init_py, re.MULTILINE
    ).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [
        dirpath
        for dirpath, _, _ in os.walk(package)
        if os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [
        (dirpath.replace(package + os.sep, "", 1), filenames)
        for dirpath, _, filenames in os.walk(package)
        if not os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend(
            [os.path.join(base, filename) for filename in filenames]
        )
    return {package: filepaths}


def parse_extras(filename):
    """Return a list of extra packages from the given file.

    Note: These packages are stored outside of the setup.py, to maintain a
    single source of truth, and allow the extras to be installed in isolation.
    """
    # Basic regex to exclude in-line comments
    re_requirement = re.compile(r"[^#]+")
    path = Path(__file__).resolve().parent.joinpath(filename)

    with open(path) as requirements_file:
        return [
            re_requirement.match(line).group(0).strip()
            for line in requirements_file
            if re_requirement.match(line)
        ]


def get_long_description():
    """Return the long package description by parsing the README file."""
    return open("README.md").read()


version = get_version(package)

coverage_extras = parse_extras("requirements-coverage.txt")
dev_extras = parse_extras("requirements-dev.txt")
mkdocs_extras = parse_extras("requirements-mkdocs.txt")
test_extras = parse_extras("requirements-test.txt")


if sys.argv[-1] == "publish":
    if os.system("pip freeze | grep wheel"):
        print("wheel not installed.\nUse `pip install wheel`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist upload")
    os.system("python setup.py bdist_wheel upload")
    print("You probably want to also tag the version now:")
    print("  git tag -a {0} -m 'version {0}'".format(version))
    print("  git push --tags")
    sys.exit()


setup(
    name=name,
    version=version,
    url=url,
    license=license,
    description=description,
    long_description=get_long_description(),
    long_description_content_type=long_description_content_type,
    author=author,
    author_email=author_email,
    packages=get_packages(package),
    package_data=get_package_data(package),
    install_requires=["hashids>1.0.0"],
    extras_require=dict(
        test=test_extras,
        dev=(test_extras + coverage_extras + mkdocs_extras + dev_extras),
    ),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
