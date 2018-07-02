# Settings
All settings are defined within the `REST_FRAMEWORK.SERIALIZER_EXTENSIONS`
sub-namespace, e.g.:

```py
# settings.py
REST_FRAMEWORK = dict(
    ...,
    SERILIZER_EXTENSIONS=dict(
        ...
    )
)
```

### Reference

**`USE_HASH_IDS`**`(bool)` <br>
Whether HashIds should be used when expanding fields.

**`HASH_IDS_SOURCE`**`(str)` <br>
A dot-delimited path string to your HashIds source within your project.

**`MAX_EXPAND_DEPTH`**`(int)` <br>
The maximum depth that any serializer can be expanded to within your
project (default: `3`).

**`QUERY_PARAMS_ENABLED`**`(bool)` <br>
Whether to allow end user to
[manipulate the filtered / expanded fields](usage-views.md)
(default: `True`).

**`AUTO_OPTIMIZE`**`(bool)` <br>
Whether to enable [automatic queryset optimization](auto-optimizations.md)
for all views (default: `False`).


# Expandable field definition
Each expandable field definition should consist of a dictionary, where the
key represents the field name, and the value is a dictionary. The exception to
this is simple ForeignKey relations, which can pass a single value representing
the serializer.

### Example
```py
class FooSerializer(ExpandableFieldsMixin)
    class Meta:
        model = foo_models.Foo
        expandable_fields = dict(
            bar=BarSerializer,
            zulu=dict(
                serializer='zulu.serializers.ZuluSerializer',
                many=True
            )
            foo_more=dict(
                serializer'foo.serializers.FooMoreSerializer',
                id_source=False,
                source='*'
            )
        )
```


### Reference

**`serializer`**`(serializers.BaseSerializer|str)` <br>
The serializer to use when the field is expanded. A dot-delimited import
string can be used to avoid circular dependency and ordering issues.

**`source`**`(Optional[str])` <br>
Can be used to pass a custom source attribute to the serializer

**`many`**`(Optional[bool])` <br>
Used to mark a *-to-many serializer relationship (default: `False`)

**`id_source`**`(Optional[str|bool])` <br>
The source to use when using ID-only expansion on a many relationship.
The boolean value `False` disables ID expansion on the field
(default: `"<field_name>_id>"`).

**`id_model`**`(Optional[str])` <br>
The model to pass to the `HashIdField` when serializing a HashId
(default: Child serializer's `Meta.model`)
