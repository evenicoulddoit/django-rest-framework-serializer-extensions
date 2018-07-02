# Automatic QuerySet optimization
Allowing your end-users to vary the API response is a very powerful feature,
but can result in extremely numerous / expensive database queries being made, depending on what is being expanded.

Luckily, extensions provides the ability to *automatically* optimize your
queryset, such that the appropriate
[`.select_related()`](https://docs.djangoproject.com/en/1.11/ref/models/querysets/#select-related) and
[`.prefetch_related()`](https://docs.djangoproject.com/en/1.11/ref/models/querysets/#prefetch-related)
calls are made as required.

## Activating
Automatic queryset optimization is an experimental feature, and is
*not applied* by default.

### Per-view
You can enable the feature for an individual view by setting the
`extensions_auto_optimize` class attribute:

```py
# views.py
class APIView(SerializerExtensionsAPIViewMixin, GenericAPIView):
    queryset = ...
    extensions_auto_optimize = True
```

The `get_extensions_auto_optimize()` method can also be used to achieve the
same result.

### Globally
Alternatively, you can enable the feature for *all views* through the
`AUTO_OPTIMIZE` setting:

```py
# settings.py
REST_FRAMEWORK = dict(
    SERIALIZER_EXTENSIONS=dict(
        AUTO_OPTIMIZE=True
    )
)
```

## Configuration
Optimizations for model to model serializer relationships are calculated
automatically. In other cases, a list of related names to select/prefetch
can be set explicitly against the field definition, and will be applied when
the field is expanded.

```py
class Serializer(SerializerExtensionsMixin, ModelSerializer):
    class Meta:
        expandable_fields = dict(
            non_model=dict(
                serializer=NonModelSerializer,
                select_related=['related_name'],
                prefetch_related=['related_name'],
            )
        )
```

In situations where automatic field optimization either fails or is unwanted,
the field definition can also be used to disable the feature:

```py
class Serializer(SerializerExtensionsMixin, ModelSerializer):
    class Meta:
        expandable_fields = dict(
            child=dict(
                serializer=ChildSerializer,
                auto_optimize=False,
            )
        )
```
