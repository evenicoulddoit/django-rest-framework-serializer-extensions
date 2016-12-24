# Django REST framework serializer extensions
**A collection of useful tools to DRY up your Django Rest Framework serializers**

Full documentation: http://django-rest-framework-serializer-extensions.readthedocs.io/

[![build-status-image]][travis]
[![coverage-status-image]][codecov]
[![pypi-version]][pypi]


## Overview
Serializer extensions reduces the need for *very similar* serializers,
by allowing the fields to be defined on a *per-view/request* basis. Fields can
be whitelisted, blacklisted, and child serializers can be optionally expanded.

Support for [HashIds](https://github.com/davidaurelio/hashids-python) is
also provided. If you're currently exposing your internal IDs over a public
API, we suggest you consider switching to HashIds instead.


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


## Basic Usage
To activate the serializer extensions, add the `SerializerExtensionsMixin` to your serializers:

```py
# serializers.py
from rest_framework.serializers import ModelSerializer
from rest_framework_serializer_extensions.serializers import SerializerExtensionsMixin

...

class OwnerSerializer(SerializerExtensionsMixin, ModelSerializer):
    class Meta:
        model = models.Owner
        fields = ('id', 'name')
        expandable_fields = dict(
            organization=OrganizationSerializer,
            cars=dict(
                serializer=SkuSerializer,
                many=True,
                source='cars.all'
            )
        )
```

And add the `SerializerExtensionsAPIViewMixin` to your API views:

```py
from rest_framework.generics import RetrieveAPIView
from rest_framework_serializer_extensions.views import SerializerExtensionsAPIViewMixin

class RetriveOwnerAPIView(SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    ...
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


[build-status-image]: https://secure.travis-ci.org/evenicoulddoit/django-rest-framework-serializer-extensions.svg?branch=master
[travis]: https://secure.travis-ci.org/evenicoulddoit/django-rest-framework-serializer-extensions?branch=master
[coverage-status-image]: https://img.shields.io/codecov/c/github/evenicoulddoit/django-rest-framework-serializer-extensions/master.svg
[codecov]: http://codecov.io/github/evenicoulddoit/django-rest-framework-serializer-extensions?branch=master
[pypi-version]: https://img.shields.io/pypi/v/djangorestframework-serializer-extensions.svg
[pypi]: https://pypi.python.org/pypi/djangorestframework-serializer-extensions
