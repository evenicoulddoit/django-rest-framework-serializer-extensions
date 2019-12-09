from django.contrib.contenttypes.models import ContentType
from django.test import override_settings, TestCase

from rest_framework_serializer_extensions import fields, utils
from test_package.test_module.serializers import TestSerializer
from tests import models
from tests.base import TEST_HASH_IDS


class ImportLocalTests(TestCase):
    """
    Unit tests for the import_local() utility method.
    """
    def test_fails_if_not_in_apps(self):
        with self.assertRaises(AssertionError):
            utils.import_local('collections.defaultdict')

    def test_fail_missing_attribute(self):
        with self.assertRaises(AttributeError):
            utils.import_local('tests.not_found')

    def test_fail_missing_module(self):
        with self.assertRaises(ImportError):
            utils.import_local('tests.not_found.not_found')

    def test_import_within_installed_apps(self):
        imported = utils.import_local(
            'rest_framework_serializer_extensions.fields.HashIdField'
        )
        self.assertIs(imported, fields.HashIdField)

    def test_import_complex_path_within_installed_apps(self):
        imported = utils.import_local(
            'test_package.test_module.serializers.TestSerializer'
        )
        self.assertIs(imported, TestSerializer)


class GetSettingTests(TestCase):
    """
    Unit tests for the get_setting() utility method.
    """
    def test_no_settings(self):
        self.assertIsNone(utils.get_setting('not_found'))

    def test_no_setting_default(self):
        self.assertTrue(utils.get_setting('not_found', True))

    @override_settings(REST_FRAMEWORK=dict())
    def test_rest_framework_settings_only(self):
        self.assertIsNone(utils.get_setting('not_found'))

    @override_settings(
        REST_FRAMEWORK=dict(
            SERIALIZER_EXTENSIONS=dict(FOO='bar')
        )
    )
    def test_extension_setting_exists(self):
        self.assertEqual('bar', utils.get_setting('FOO'))

    @override_settings(REST_FRAMEWORK=dict(SERIALIZER_EXTENSIONS=dict()))
    def test_extension_setting_does_not_exist(self):
        self.assertIsNone(utils.get_setting('FOO'))


class GetHashIdsSourceTests(TestCase):
    """
    Unit tests for the get_hash_ids_source() utility method.
    """
    def test_unset_raises(self):
        with self.assertRaisesRegex(AssertionError, 'No HASH_IDS_SOURCE'):
            utils.get_hash_ids_source()

    @override_settings(
        REST_FRAMEWORK=dict(
            SERIALIZER_EXTENSIONS=dict(
                HASH_IDS_SOURCE='tests.DOES_NOT_EXIST'
            )
        )
    )
    def test_source_not_found(self):
        with self.assertRaises(AttributeError):
            utils.get_hash_ids_source()

    @override_settings(
        REST_FRAMEWORK=dict(
            SERIALIZER_EXTENSIONS=dict(
                HASH_IDS_SOURCE='tests.base.TEST_HASH_IDS'
            )
        )
    )
    def test_returns_valid_source(self):
        source = utils.get_hash_ids_source()
        self.assertIs(TEST_HASH_IDS, source)


@override_settings(
    REST_FRAMEWORK=dict(
        SERIALIZER_EXTENSIONS=dict(
            HASH_IDS_SOURCE='tests.base.TEST_HASH_IDS'
        )
    )
)
class InternalIdFromModelAndExternalIdTests(TestCase):
    """
    Unit tests for the internal_id_from_model_and_external_id() utility method.
    """
    def test_bad_external_id(self):
        """
        Test when a bad external ID is given, an ObjectDoesNotExist is raised.

        The exist DoestNotExist is inferred from the model.
        """
        with self.assertRaises(models.CarModel.DoesNotExist):
            utils.internal_id_from_model_and_external_id(
                models.CarModel, "bad data"
            )

    def test_external_id_for_different_model(self):
        """
        Test if the external ID doesn't match the model, we raise an exception.
        """
        ct_org = ContentType.objects.get_for_model(models.Organization)
        org = models.Organization.objects.create(name='a')
        external_id = utils.get_hash_ids_source().encode(ct_org.pk, org.pk)

        # We external ID does match an internal ID, but not for this Model.
        with self.assertRaises(models.CarModel.DoesNotExist):
            utils.internal_id_from_model_and_external_id(
                models.CarModel, external_id
            )

    def test_returns_valid_internal_id(self):
        """
        Test valid Model/External ID combinations return internal IDs.

        The external ID is composed of the primary keys for the instance and
        the model's ContentType.
        """
        ct_org = ContentType.objects.get_for_model(models.Organization)
        org_a = models.Organization.objects.create(name='a')
        org_b = models.Organization.objects.create(name='b')

        external_id_a = utils.get_hash_ids_source().encode(ct_org.pk, org_a.pk)
        self.assertEqual(
            org_a.pk,
            utils.internal_id_from_model_and_external_id(
                models.Organization, external_id_a
            )
        )

        external_id_b = utils.get_hash_ids_source().encode(ct_org.pk, org_b.pk)
        self.assertEqual(
            org_b.pk,
            utils.internal_id_from_model_and_external_id(
                models.Organization, external_id_b
            )
        )


class ModelFromDefinitionTests(TestCase):
    """
    Unit tests for the model_from_definition() utility method.
    """
    def test_pass_non_model_class_raises_assertion_error(self):
        """
        An error should be raised when a non-Django model class is passed.
        """
        with self.assertRaisesRegex(AssertionError, 'not a Django model'):
            utils.model_from_definition(dict)

    def test_pass_string_as_model_definition(self):
        """
        Passing string corresponding to model should import and return model.
        """
        self.assertEqual(
            models.CarModel,
            utils.model_from_definition('tests.models.CarModel')
        )

    def test_pass_model_class_as_model_definition(self):
        """
        Test that the method returns its argument when Django model is passed.
        """
        self.assertEqual(
            models.CarModel, utils.model_from_definition(models.CarModel)
        )
