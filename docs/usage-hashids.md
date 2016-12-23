# Enabling HashIds
Serializer extensions also provides support for
[HashIds](https://github.com/davidaurelio/hashids-python). Publicly exposing
database IDs to your end users is often not a good idea, as it both reveals the
number of entries (e.g. customers, orders etc.) in your database, and makes
misuse of vulnerable endpoints a lot easier when a sequential key is used (e.g.
`/customers/1/`). HashIds aim to solve both issues.

To enable HashIds, add the following to your `REST_FRAMEWORK` setting:

```py
# settings.py
REST_FRAMEWORK = dict(
    SERIALIZER_EXTENSIONS=dict(
        USE_HASH_IDS=True,
        HASH_IDS_SOURCE='my_app.HASH_IDS'
    )
)

# my_app/__init__.py
import hashids
HASH_IDS = hashids.Hashids(salt='MYSALT')
```

Expanded ID fields will now use HashIds:

```py
# serializers.py
class OwnerSerializer(SerializerExtensionsMixin, ModelSerializer):
    class Meta:
        model = models.Owner
        fields = ('name',)
        expandable_fields = dict(
            organization=OrganizationSerializer,
        )
```

```js
>>> GET /owners/xFj/
{
  "name": "Tyrell",
  "organization_id": "4Vd"
}
```

# HashIdField
You can serialize HashIds as and when required using the `HashIdField`:

```py
...
from rest_framework.serializers import ModelSerializer
from rest_framework_serializer_extensions.fields import HashIdField

from app import models


class OwnerSerializer(ModelSerializer):
    id = HashIdField(model=models.Owner)

    class Meta:
        model = models.Owner
        fields = ('id', 'name')
```

The `model` argument is used in combination with the source to generate the
HashId. The field will automatically handle serializing/deserializing
external HashIds to internal numeric IDs.


# Additional fields
Also provided are the `HashIdHyperlinkedIdentityField` and
`HashIdHyperlinkedRelatedField` fields. As above, these require a `model`
argument.
