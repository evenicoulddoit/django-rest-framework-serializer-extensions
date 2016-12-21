import importlib

from django.conf import settings
from django.contrib.contenttypes.models import ContentType


def import_local(path_to_object):
    """
    Import an object from within the Django app.

    After importing, the user should perform sanity checks on the type of
    object that was actually imported for additional security.
    """
    path, name = path_to_object.rsplit('.', 1)

    app = path.split('.')[0]

    if app not in settings.INSTALLED_APPS:
        raise AssertionError(
            "Cannot import from outside installed apps"
        )

    return getattr(importlib.import_module(path), name)


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

    return import_local(source_str)


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
