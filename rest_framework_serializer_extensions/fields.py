from django.core.exceptions import ObjectDoesNotExist
from django.utils import six
from rest_framework.fields import Field
from rest_framework.relations import (
    HyperlinkedIdentityField, HyperlinkedRelatedField)

from rest_framework_serializer_extensions import utils


class GetHashIdModelMixin(object):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', None)
        super(GetHashIdModelMixin, self).__init__(*args, **kwargs)

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
                return getattr(self.parent, custom_fn_name)()
            else:
                try:
                    return self.parent.Meta.model
                except AttributeError:
                    raise AssertionError(
                        'No "model" value passed to field "{0}"'
                        .format(type(self).__name__)
                    )
        elif isinstance(self.model, six.string_types):
            return utils.model_from_definition(self.model)
        else:
            return self.model


class HashIdField(GetHashIdModelMixin, Field):
    """
    Represent an external ID (using HashIds).

    Requires the source of the field to be an internal ID, and to provide
    a "model" keyword argument. Together these will produce the external ID.
    """
    default_error_messages = {
        'malformed_hash_id': 'That is not a valid HashId',
    }

    def to_representation(self, value):
        return utils.external_id_from_model_and_internal_id(
            self.get_model(), value
        )

    def to_internal_value(self, value):
        model = self.get_model()
        try:
            return utils.internal_id_from_model_and_external_id(model, value)
        except ObjectDoesNotExist:
            self.fail('malformed_hash_id')


class HashedHyperlinkMixin(GetHashIdModelMixin):
    def get_url(self, obj, view_name, request, fmt):
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
            view_name, kwargs=kwargs, request=request, format=fmt
        )


class HashIdHyperlinkedIdentityField(
    HashedHyperlinkMixin, HyperlinkedIdentityField
):
    pass


class HashIdHyperlinkedRelatedField(
    HashedHyperlinkMixin, HyperlinkedRelatedField
):
    pass
