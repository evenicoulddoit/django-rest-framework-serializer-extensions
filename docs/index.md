<div class="badges">
    <a href="http://travis-ci.org/evenicoulddoit/django-rest-framework-serializer-extensions">
        <img src="https://travis-ci.org/evenicoulddoit/django-rest-framework-serializer-extensions.svg?branch=master">
    </a>
    <a href="https://pypi.python.org/pypi/djangorestframework-serializer-extensions">
        <img src="https://img.shields.io/pypi/v/djangorestframework-serializer-extensions.svg">
    </a>
</div>


# Django REST framework serializer extensions
**A collection of useful tools to DRY up your Django Rest Framework serializers**


## Overview
Serializer extensions reduces the need for *very similar* serializers,
by allowing the fields to be defined on a *per-view/request* basis. Fields can
be whitelisted, blacklisted, and child serializers can be optionally expanded.

Support for [HashIds](https://github.com/davidaurelio/hashids-python) is
also provided. If you're currently exposing your internal IDs over a public
API, we suggest you consider switching to HashIDs instead.


## Requirements
* Python (2.7, 3.4, 3.5)
* [Django](https://github.com/tomchristie/django-rest-framework) (1.8, 1.9, 1.10)
* [Django REST Framework](https://github.com/tomchristie/django-rest-framework) (3.3, 3.4, 3.5)
* [HashIds](https://github.com/davidaurelio/hashids-python) (>1.0)


## Installation
Install using `pip`:

```bash
$ pip install djangorestframework-serializer-extensions
```

And add `rest_framework_serializer_extensions` to your `INSTALLED_APPS` setting:

```py
INSTALLED_APPS = (
    ...
    'rest_framework_serializer_extensions'
)
```


## Examples
Serializer extensions allows your API to re-use your serializers to fit a
variety of use cases. The examples shown below use query parameters to
modify the response, but individual views can interact with your serializers
in much the same way.

```js
>>> GET /owner/x4F/
{
  "id": 'x4F',
  "name": 'tyrell',
  "organization_id": 'kgD'
}
```

```js
>>> GET /owner/x4F/?expand=organization
{
  "id": 'x4F',
  "name": 'tyrell',
  "organization_id": 'kgD',
  "organization": {
    "id": "kgD",
    "name": "E Corp"
  }
}
```

```js
>>> GET /owner/x4F/?expand=cars__model&exclude=name
{
  "id": 'x4F',
  "organization_id": 'kgD',
  "cars": [
    {
      "id": "wf9",
      "variant": "P100D",
      "model": {
        "id": "ncX",
        "name": "Model S"
      }
    }
  ]
}
```

```js
>>> GET /owner/x4F/?expand=cars&only=cars__variant
{
  "cars": [
    {
      "variant": "P100D",
    }
  ]
}
```


## Testing
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


## Documentation
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
