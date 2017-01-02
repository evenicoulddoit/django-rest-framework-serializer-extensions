# Examples
Serializer extensions allows your API to re-use your serializers to fit a
variety of use cases. Take the following serializers:


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

With no changes, our endpoint returns:

```js
>>> GET /owner/x4F/
{
  "id": 'x4F',
  "name": 'tyrell',
  "organization_id": 'kgD'
}
```

We can expand our ForeignKey to organization:

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

And our many relationship to cars:

```js
>>> GET /owner/x4F/?expand=cars
{
  "id": 'x4F',
  "name": "tyrell",
  "organization_id": 'kgD',
  "cars": [
    {
      "id": "wf9",
      "variant": "P100D",
      "model_id": "ncX"
    }
  ]
}
```

We can perform nested expansion:

```js
>>> GET /owner/x4F/?expand=cars__model__manufacturer
{
  "id": 'x4F',
  "name": "tyrell",
  "organization_id": 'kgD',
  "cars": [
    {
      "id": "wf9",
      "variant": "P100D",
      "model": {
        "id": "ncX",
        "name": "Model S"
        "manufacturer_id": "qMn",
        "manufacturer": {
          "id": "qMn",
          "name": "Tesla"
        }
      }
    }
  ]
}
```

We can exclude certain fields

```js
>>> GET /owner/x4F/?expand=cars__model__manufacturer&exclude=name,cars__id
{
  "id": 'x4F',
  "organization_id": 'kgD',
  "cars": [
    {
      "variant": "P100D",
      "model": {
        "id": "ncX",
        "name": "Model S"
        "manufacturer_id": "qMn",
        "manufacturer": {
          "id": "qMn",
          "name": "Tesla"
        }
      }
    }
  ]
}
```

Or include only the ones we want


```js
>>> GET /owner/x4F/?expand=cars__model__manufacturer&only=name,cars__model__manufacturer__name
{
  "name": "tyrell",
  "cars": [
    {
      "model": {
        "manufacturer": {
          "name": "Tesla"
        }
      }
    }
  ]
}
```

These examples all use query parameters to modify the response,
[individual views can interact with your serializers in much the same way](usage-views.md).
