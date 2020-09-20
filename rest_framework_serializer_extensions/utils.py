from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.module_loading import import_string


def get_setting(key, default=None):
    try:
        return settings.REST_FRAMEWORK['SERIALIZER_EXTENSIONS'][key]
    except (AttributeError, KeyError):
        return default


def get_hash_ids_source():
    """
    Return the HashIds instance used to (de)serialize external IDs.
    """
    source_str = get_setting('HASH_IDS_SOURCE')

    if not source_str:
        raise AssertionError('No HASH_IDS_SOURCE setting configured.')

    return import_string(source_str)


def external_id_from_model_and_internal_id(model, internal_id):
    """
    Return a hash for the model and internal ID combination.
    """
    return get_hash_ids_source().encode(
        ContentType.objects.get_for_model(model).id, internal_id
    )


def internal_id_from_model_and_external_id(model, external_id):
    """
    Return the internal ID from the external ID and model combination.

    Because the HashId is a combination of the model's content type and the
    internal ID, we validate here that the external ID decodes as expected,
    and that the content type corresponds to the model we're expecting.
    """
    try:
        content_type_id, instance_id = get_hash_ids_source().decode(
            external_id)
    except (TypeError, ValueError):
        raise model.DoesNotExist

    content_type = ContentType.objects.get_for_id(content_type_id)

    if content_type.model_class() != model:
        raise model.DoesNotExist

    return instance_id


def model_from_definition(model_definition):
    """
    Return a Django model corresponding to model_definition.

    Model definition can either be a string defining how to import the model,
    or a model class.

    Arguments:
        model_definition: (str|django.db.models.Model)

    Returns:
        (django.db.models.Model)
    """
    if isinstance(model_definition, str):
        model = import_string(model_definition)
    else:
        model = model_definition

    try:
        assert issubclass(model, models.Model)
    except (AssertionError, TypeError):
        raise AssertionError(
            '"{0}"" is not a Django model'.format(model_definition)
        )

    return model
