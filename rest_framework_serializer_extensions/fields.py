from django.db import models
from rest_framework.fields import Field
from rest_framework.relations import (
    HyperlinkedIdentityField, HyperlinkedRelatedField)

from rest_framework_serializer_extensions import utils


class GetHashIdModelMixin(object):
    def get_model(self):
        """
        Return the model to generate the HashId for.

        By default, this will equal the model defined within the Meta of the
        ModelSerializer, but can be redefined either during initialisation
        of the Field, or by providing a get_<field_name>_model method on the
        parent serializer.

        The Meta can either explicitly define a model, or provide a
        dot-delimited string path to it.
        """
        if self.model is None:
            custom_fn_name = 'get_{0}_model'.format(self.field_name)

            if hasattr(self.parent, custom_fn_name):
                return getattr(self.parent, custom_fn_name)
            else:
                return self.parent.Meta.model
        elif isinstance(self.model, basestring):
            obj = utils.import_local(self.model)
            assert issubclass(obj, models.Model), (
                '{0} is not a Django model'.format(self.model)
            )
            return obj
        else:
            return self.model


class HashIdField(GetHashIdModelMixin, Field):
    """
    Represent an external ID (using HashIds).

    Requires the source of the field to be an internal ID, and to provide
    a "model" keyword argument. Together these will produce the external ID.
    """
    allow_null = True

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', None)
        super(HashIdField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        return utils.external_id_from_model_and_internal_id(
            self.get_model(), value
        )

    def to_internal_value(self, value):
        return utils.internal_id_from_model_and_external_id(
            self.get_model(), value
        )


class HashIdListField(HashIdField):
    """
    Return a list of external IDs (using HashIds).

    The "source" here should point to an iterable (e.g. a QuerySet),
    and the keyword "individual_source" (defaults to "id") should be specified
    to provide the source to each HashIdField.
    """
    def __init__(self, *args, **kwargs):
        self.individual_source = kwargs.pop('individual_source', 'id')
        super(HashIdListField, self).__init__(*args, **kwargs)

    def to_representation(self, values):
        return [
            super(HashIdListField, self).to_representation(
                getattr(value, self.individual_source)
            )
            for value in values
        ]

    def to_internal_value(self, values):
        return [
            super(HashIdListField, self).to_internal_value(
                getattr(value, self.individual_source)
            )
            for value in values
        ]


class HashedHyperlinkMixin(GetHashIdModelMixin):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', None)
        super(HashedHyperlinkMixin, self).__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Use the field source in combination with the model to generate the URL.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None

        external_id = utils.external_id_from_model_and_internal_id(
            self.get_model(),
            getattr(obj, self.lookup_field)
        )
        kwargs = {self.lookup_url_kwarg: external_id}
        return self.reverse(
            view_name, kwargs=kwargs, request=request, format=format
        )


class HashIdHyperlinkedIdentityField(
    HashedHyperlinkMixin, HyperlinkedIdentityField
):
    pass


class HashIdHyperlinkedRelatedField(
    HashedHyperlinkMixin, HyperlinkedRelatedField
):
    pass
