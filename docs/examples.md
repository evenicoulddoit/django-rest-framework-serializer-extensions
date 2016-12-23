# Examples
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
