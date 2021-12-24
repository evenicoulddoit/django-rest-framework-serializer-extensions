# The view mixin
Just as with our serializers, our API views require a mixin to support the
extensions - the `SerializerExtensionsAPIViewMixin` class. Your views will now
look something like:

```py
from rest_framework.generics import RetrieveAPIView
from rest_framework_serializer_extensions.views import SerializerExtensionsAPIViewMixin

from app import models


class RetrieveOwnerAPIView(SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    queryset = models.Owner.objects.all()
    serializer_class = OwnerSerializer
    ...
```

By adding the mixin, all of the serializer extensions are now supported.
Your end users can now control exactly what is serialized through query
parameters:

```js
>>> GET /owner/1/?expand=cars__model&exclude=name
{
  "id": 1,
  "organization_id": 1,
  "cars": [
    {
      "id": 1,
      "variant": "P100D",
      "model": {
        "id": 1,
        "name": "Model S"
      }
    }
  ]
}
```

# View-based context
The above example works on a *per-request* basis, but you can set up your
view to control the serializer context too:

```py
# Using fixed attributes
class FixedAPIView(SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    queryset = models.Owner.objects.all()
    serializer_class = OwnerSerializer
    extensions_expand = {'organization'}
    extensions_expand_id_only = {'cars'}
    extensions_exclude = set()
    extensions_only = set()


# Or calculated
class DynamicAPIView(SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    queryset = models.Owner.objects.all()
    serializer_class = OwnerSerializer

    def get_extensions_mixin_context(self):
        context = super(DynamicAPIView, self).get_extensions_mixin_context()
        context['expand'] = set([
            field_name for field_name in context['expand']
            if field_name != 'prevent_expansion'
        ])
        return context
```

Whilst the view sets the *defaults*, the extension context can be overridden
by the end using through query parameters.

# Disabling query parameter modification
You can disable users from modifying the serialized result:

```py
# Using a fixed attribute
class FixedAPIView(SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    extensions_query_params_enabled = False


# Or depending on the request context
class PossiblyFixedAPIView(SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    def get_extensions_query_params_enabled(self):
        return random.choice([True, False])
```

Alternatively, you can also disable the feature globally through the
`QUERY_PARAMS_ENABLED` setting:

```py
# settings.py
REST_FRAMEWORK = dict(
    SERIALIZER_EXTENSIONS=dict(
        QUERY_PARAMS_ENABLED=False
    )
)
```
