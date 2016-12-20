Django REST framework serializer extensions
===========================================

[![build-status-image]][travis]
[![coverage-status-image]][codecov]
[![pypi-version]][pypi]


Overview
========

**A collection of useful tools to DRY up your Django Rest Framework serializers**

Requirements
============

-   Python (2.7, 3.3, 3.4)
-   Django (1.8, 1.9, 1.10)
-   Django REST Framework (3.3, 3.4, 3.5)

Installation
============

Install using `pip`…

```bash
$ pip install djangorestframework-serializer-extensions
```

Example
=======

TODO: Write example.

Testing
=======

Install testing requirements.

```bash
$ pip install -r requirements.txt
```

Run with runtests.

```bash
$ ./runtests.py
```

You can also use the excellent
[tox](http://tox.readthedocs.org/en/latest/) testing tool to run the
tests against all supported versions of Python and Django. Install tox
globally, and then simply run:

```bash
$ tox
```

Documentation
=============

To build the documentation, you’ll need to install `mkdocs`.

```bash
$ pip install mkdocs
```

To preview the documentation:

```bash
$ mkdocs serve
Running at: http://127.0.0.1:8000/
```

To build the documentation:

```bash
$ mkdocs build
```


[build-status-image]: https://secure.travis-ci.org/evenicoulddoit/django-rest-framework-serializer-extensions.svg?branch=master
[travis]: https://secure.travis-ci.org/evenicoulddoit/django-rest-framework-serializer-extensions?branch=master
[coverage-status-image]: https://img.shields.io/codecov/c/github/evenicoulddoit/django-rest-framework-serializer-extensions/master.svg
[codecov]: http://codecov.io/github/evenicoulddoit/django-rest-framework-serializer-extensions?branch=master
[pypi-version]: https://img.shields.io/pypi/v/djangorestframework-serializer-extensions.svg
[pypi]: https://pypi.python.org/pypi/djangorestframework-serializer-extensions
