from django.test import override_settings, RequestFactory, TestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer, ModelSerializer

from rest_framework_serializer_extensions import fields, utils
from tests import models


"""
START TEST SERIALIZERS
"""


class CarModelTestSerializer(ModelSerializer):
    """
    A basic ModelSerializer using a HashIdField.
    """
    id = fields.HashIdField()

    class Meta:
        model = models.CarModel
        fields = ('id', 'name')


class CarModelMethodTestSerializer(ModelSerializer):
    """
    A ModelSerializer using a method to retrieve the model for a HashIdField.
    """
    manufacturer_id = fields.HashIdField()

    class Meta:
        model = models.CarModel
        fields = ('id', 'name', 'manufacturer_id')

    def get_manufacturer_id_model(self):
        return models.Manufacturer


"""
END TEST SERIALIZERS
"""


@override_settings(
    REST_FRAMEWORK=dict(
        SERIALIZER_EXTENSIONS=dict(
            HASH_IDS_SOURCE='tests.base.TEST_HASH_IDS'
        )
    )
)
class BaseFieldsTestCase(TestCase):
    def setUp(self):
        self.manufacturer = models.Manufacturer.objects.create(
            name='Manufacturer'
        )
        self.car_model = models.CarModel.objects.create(
            name='Model',
            manufacturer=self.manufacturer
        )

    def external_id(self, instance):
        return utils.external_id_from_model_and_internal_id(
            type(instance), instance.pk
        )


class HashIdFieldTests(BaseFieldsTestCase):
    """
    Unit tests for the HashIdField
    """
    def test_representation_requires_model(self):
        with self.assertRaisesRegex(AssertionError, 'No "model"'):
            fields.HashIdField().to_representation(self.car_model.pk)

    def test_representation_explicit_model_object(self):
        representation = (
            fields.HashIdField(model=models.CarModel)
            .to_representation(self.car_model.pk)
        )
        self.assertEqual(self.external_id(self.car_model), representation)

    def test_representation_explicit_model_reference(self):
        representation = (
            fields.HashIdField(model='tests.models.CarModel')
            .to_representation(self.car_model.pk)
        )
        self.assertEqual(self.external_id(self.car_model), representation)

    def test_representation_explicit_invalid_model_reference(self):
        with self.assertRaisesRegex(AssertionError, 'not a Django model'):
            (
                fields.HashIdField(model='tests.base.TEST_HASH_IDS')
                .to_representation(self.car_model.pk)
            )

    def test_representation_implicit_model_reference_through_meta(self):
        """
        Test the model defined within the Meta of the serializer can be used.
        """
        field = CarModelTestSerializer().fields['id']
        representation = field.to_representation(self.car_model.pk)
        self.assertEqual(self.external_id(self.car_model), representation)

    def test_representation_explicit_model_serializer_method(self):
        """
        Test that a method on the serializer can be used to retrieve the model.
        """
        field = CarModelMethodTestSerializer().fields['manufacturer_id']
        representation = field.to_representation(self.manufacturer.pk)
        self.assertEqual(self.external_id(self.manufacturer), representation)

    def test_internal_value_requires_model(self):
        with self.assertRaisesRegex(AssertionError, 'No "model"'):
            fields.HashIdField().to_internal_value(
                self.external_id(self.car_model)
            )

    def test_internal_value_explicit_model_object(self):
        internal_value = (
            fields.HashIdField(model=models.CarModel)
            .to_internal_value(self.external_id(self.car_model))
        )
        self.assertEqual(self.car_model.pk, internal_value)

    def test_internal_value_explicit_model_reference(self):
        internal_value = (
            fields.HashIdField(model='tests.models.CarModel')
            .to_internal_value(self.external_id(self.car_model))
        )
        self.assertEqual(self.car_model.pk, internal_value)

    def test_internal_value_explicit_invalid_model_reference(self):
        with self.assertRaisesRegex(AssertionError, 'not a Django model'):
            (
                fields.HashIdField(model='tests.base.TEST_HASH_IDS')
                .to_internal_value(self.external_id(self.car_model))
            )

    def test_internal_value_hash_id_validation(self):
        with self.assertRaisesRegex(ValidationError, 'not a valid HashId'):
            (
                fields.HashIdField(model='tests.models.CarModel')
                .to_internal_value('abc123')
            )

    def test_internal_value_implicit_model_reference_through_meta(self):
        """
        Test the model defined within the Meta of the serializer can be used.
        """
        field = CarModelTestSerializer().fields['id']
        internal_value = field.to_internal_value(
            self.external_id(self.car_model)
        )
        self.assertEqual(self.car_model.pk, internal_value)

    def test_internal_value_explicit_model_serializer_method(self):
        """
        Test that a method on the serializer can be used to retrieve the model.
        """
        field = CarModelMethodTestSerializer().fields['manufacturer_id']
        internal_value = field.to_internal_value(
            self.external_id(self.manufacturer)
        )
        self.assertEqual(self.manufacturer.pk, internal_value)


class HashIdHyperlinkedIdentityFieldTests(BaseFieldsTestCase):
    """
    Unit tests for the HashIdHyperlinkedIdentityField.
    """
    def setUp(self):
        super(HashIdHyperlinkedIdentityFieldTests, self).setUp()

        class TestSerializer(Serializer):
            manufacturer = fields.HashIdHyperlinkedIdentityField(
                lookup_url_kwarg='external_id',
                model=models.Manufacturer,
                view_name='car_model',
            )

        self.Serializer = TestSerializer
        self.context = dict(request=RequestFactory().get('/'))

    def test_unsaved_model_returns_none(self):
        """
        Test as with the vanilla field, unsaved instances return None.
        """
        unsaved = models.CarModel(
            name='Unsaved car',
            manufacturer=models.Manufacturer(name='Unsaved manufacturer')
        )
        serialized = self.Serializer(unsaved, context=self.context).data
        self.assertIsNone(serialized['manufacturer'])

    def test_uses_external_id(self):
        """
        Test behaves like vanilla field, but uses a HashId.
        """
        serialized = self.Serializer(self.car_model, context=self.context).data
        expected_path = reverse(
            'car_model', args=(self.external_id(self.manufacturer),)
        )
        self.assertEqual(
            serialized['manufacturer'],
            'http://testserver{0}'.format(expected_path)
        )
