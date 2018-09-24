# The serializer mixin
To activate the serializer extensions, apply the `SerializerExtensionsMixin`
class to your serializers:

```py
# serializers.py
from rest_framework.serializers import ModelSerializer
from rest_framework_serializer_extensions.serializers import SerializerExtensionsMixin


class OwnerSerializer(SerializerExtensionsMixin, ModelSerializer):
    ...
```

This enables the "only" and "exclude" features, which allow you to
whitelist/blacklist fields as required, and provides a few helper methods.


# Creating expandable fields
One of the core aims of this project is to reduce the need to create multiple
serializers to represent a single model. The expandable fields feature is
probably the most significant way in which this aim can be achieved. Imagine
you've defined the following serializers:


```py
# old_serializers.py

class OwnerSerializer(ModelSerializer):
    class Meta:
        model = models.Owner
        fields = ('id', 'name')


class OwnerWithOrganizationSerializer(ModelSerializer):
    organization = OrganizationSerializer()

    class Meta:
        model = models.Owner
        fields = ('id', 'name', 'organization')


class OwnerWithCarsSerializer(ModelSerializer):
    cars = SkuSerializer(many=True)

    class Meta:
        model = models.Owner
        fields = ('id', 'name', 'cars')
```

As your API grows you may find situations in which you need to serialize an
instance with some of it's foreign relations, and situations where you don't.
For efficiency reasons you end up creating multiple serializers, each with a
very specific task. This can quickly grow out of hand, and lead to
inconsistencies.

We can solve this by using *expandable fields*. Here's how we could modify the
serializers above to advantage of them:

```py
class OwnerSerializer(SerializerExtensionsMixin, ModelSerializer):
    class Meta:
        model = models.Owner
        fields = ('id', 'name')
        expandable_fields = dict(
            organization=OrganizationSerializer,
            cars=dict(
                serializer=SkuSerializer,
                many=True
            )
        )
```

Our one serializer now handles all 3 use cases. If we want to serialize an
owner along with their organization, their cars, or both, we can do so.


## Single child expansion
A serialized owner instance will now look something like:

```js
{
    "id": 1,
    "name": "Tyrell",
    "organization_id": 1
}
```

The expandable fields mixin automatically adds an ID reference to the output,
mimicing the ForeignKey API of Django models. This consistency provides users
of your API with just enough information to make further queries if required,
whilst maintaining the efficiency of your serializer.

Your child serializer can now be expanded, to produce:

```js
{
    "id": 1,
    "name": "Tyrell",
    "organization_id": 1,
    "organization": {
        "id": 1,
        "name": "E Corp"
    }
}
```


### OneToOne Reverse ForeignKeys
You may want to create an expandable field for a OneToOne relationship where
the relation is stored on the other instance's table. Here, no `_id` field
will be present on your model, and so the only way to retrieve the ID is to
perform an additional database query (or use a `select_related()` join).
In these situations, you can use the `id_source` property in your expandable
field definition to determine what happens:

```py
# models.py
class Owner(models.Model):
    ...

class OwnerBio(models.Model):
    owner = models.OneToOneField(Owner)
    ...

# serializers.py
class OwnerSerializer(SerializerExtensionsMixin, ModelSerializer):
    class Meta:
        ...
        expandable_fields = dict(
            bio=dict(
                serializer=OwnerBioSerializer,
                id_source='bio.pk'
            )
```

Setting `id_source=False` results in no ID field being included.


### Writable ForeignKey relationships
In some cases it may be appropriate to allow ForeignKey fields to be set during
a create or an update via your API. To create a ForeignKey relation that is
both expandable and writable, set `read_only=False` in its definition.

```py
# serializers.py
class OwnerSerializer(SerializerExtensionsMixin, ModelSerializer):
    class Meta:
        model = models.Owner
        fields = ('id', 'name')
        expandable_fields = dict(
            organization=dict(
                serializer=OrganizationSerializer,
                read_only=False
            )
        )
```

As usual, the above serializer will have an `organization_id` field by default.
To set or alter the organization of an owner, pass a value to this field:

```js
>>> POST /owner/2/
{
  "name": "Elliot",
  "organization_id": 3
}
```

It is important to note that we are passing an organization's ID to the
`organization_id` field, not a dictionary of properties to the `organization`
field.

To support nullable foreign key relationship in writable situation, set `allow_null=True` after `read_only=False`.

During validation the serializer will find the corresponding organization and
add make it available in the deserialized data under the key
`organization_id_resolved`:

```py
{
    "name": "Elliot",
    "organization_id": 2,
    "organization_id_resolved": <Organization: Allsafe>
}
```


### Non-Model relations
Any child serializer can be expanded, not just Django model relations.
A common use case for expanding fields is to avoid serializing unnecessary,
perhaps time-consuming to compute, fields.


## Multiple child expansion
As highlighted in our first example at the top of this section, you can also
expand *-to-many relationships. You may have noticed that by default however,
no IDs are provided, as doing so would necessarily require a further database
query (or a `prefetch_related()` on the initial queryset). Instead, many
relationships must be expanded explicitly, resulting in something like:

```py
{
    "id": 1,
    "name": "Tyrell",
    "organization_id": 1,
    "cars": [
        {
            "id": 1,
            "variant": "P100D",
            "model_id": 1
        }
    ]
}
```

### ID-only expansion
For many relationships, the option to expand by ID only is also provided. In
the previous example, this would yield:

```py
{
    "id": 1,
    "name": "Tyrell",
    "organization_id": 1,
    "cars": [1]
}
```

## Custom expansion
In certain situations you may wish to optionally serialize a complex or
computed value. This can be achieved by using a `SerializerMethodField`:

```
class OwnerSerializer(SerializerExtensionsMixin, ModelSerializer):
    class Meta:
        model = models.Owner
        fields = ('id', 'name')
        expandable_fields = dict(
            status=serializers.SerializerMethodField,,
            bio=serializer=SerializerMethodField
        )

    def get_status(self, owner):
        # Complicated computations...
        return True

    def get_bio(self, owner):
        # See full API documentation for more
        if owner.show_bio:
            return self.represent_child(
                name='bio',
                serializer=OwnerBioSerializer,
                instance=owner.bio
            )
```


## Nested expansion
You can expand fields on child serializers too (provided they also take
advantage of the `SerializerExtensionsMixin`). By doing so, we can achieve
something like the following:

```js
{
    "id": 1,
    "name": "Tyrell",
    "organization_id": 1,
    "cars": [
        {
            "id": 1,
            "variant": "P100D",
            "model_id": 1,
            "model": {
                "id": 1,
                "name": "Model S",
                "manufacturer_id": 1,
                "manufacturer": {
                    "id": 1,
                    "name": "Telsa"
                }
            }
        }
        }
    ]
}
```


## It's all in the context
Now that you've redesigned your serializers, you're probably going to want to
take advantage of the extra features. Our serialized data depends
on the context passed to our serializer (in particular, the
`only`, `exclude`, `expand` and `expand_id_only` iterables). For this, you'll
need to [make a few changes to your API views](usage-views.md).
