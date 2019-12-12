from rest_framework import serializers

from rest_framework_serializer_extensions.serializers import ExcludeFieldsMixin
from tests import models
from tests.base import SerializerMixinTestCase


"""
START TEST SERIALIZERS
"""


class OrganizationTestSerializer(
    ExcludeFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        fields = ('id', 'name')
        model = models.Organization


class OwnerTestSerializer(ExcludeFieldsMixin, serializers.ModelSerializer):
    organization = OrganizationTestSerializer()

    class Meta:
        fields = ('id', 'name', 'email', 'organization')
        model = models.Owner


class SkuTestSerializer(ExcludeFieldsMixin, serializers.ModelSerializer):
    owners = OwnerTestSerializer(many=True)

    class Meta:
        fields = ('id', 'variant', 'owners')
        model = models.Sku


class ManufacturerTestSerializer(
    ExcludeFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        fields = ('id', 'name')
        model = models.Manufacturer


class CarModelTestSerializer(ExcludeFieldsMixin, serializers.ModelSerializer):
    skus = SkuTestSerializer(many=True)
    manufacturer = ManufacturerTestSerializer()

    class Meta:
        fields = ('id', 'name', 'skus', 'manufacturer')
        model = models.CarModel


"""
END TEST SERIALIZERS
"""


class ExcludeFieldsSerializerMixinTests(SerializerMixinTestCase):
    """
    Functional tests for the ExcludeFieldsSerializerMixin.

    By passing an "exclude" iterable to the serializer's context, the specified
    fields should be excluded from serialization.
    """
    def serialize(self, **context):
        """
        Return the serialized car with the given context applied
        """
        return (
            CarModelTestSerializer(self.carmodel_model_s, context=context)
            .data
        )

    def test_no_exclude_implicit(self):
        self.assertDictEqual(self.serialize(), self.expected_complete_data)

    def test_no_exclude_explicit(self):
        self.assertDictEqual(
            self.serialize(exclude=set()),
            self.expected_complete_data
        )

    def test_exclude_single_root_field(self):
        expected = dict(self.expected_complete_data)
        del expected['id']
        self.assertDictEqual(self.serialize(exclude={'id'}), expected)

    def test_exclude_multiple_root_fields(self):
        expected = dict(self.expected_complete_data)
        del expected['id']
        del expected['name']
        self.assertDictEqual(self.serialize(exclude={'id', 'name'}), expected)

    def test_exclude_serializer_foreign_key_field(self):
        expected = dict(self.expected_complete_data)
        del expected['manufacturer']
        self.assertDictEqual(
            self.serialize(exclude={'manufacturer'}), expected
        )

    def test_exclude_serializer_many_field(self):
        expected = dict(self.expected_complete_data)
        del expected['skus']
        self.assertDictEqual(self.serialize(exclude={'skus'}), expected)

    def test_exclude_single_child_field_foreign_key(self):
        expected = dict(self.expected_complete_data)
        del expected['manufacturer']['id']
        self.assertDictEqual(
            self.serialize(exclude={'manufacturer__id'}), expected
        )

    def test_exclude_multiple_child_fields_foreign_key(self):
        expected = dict(self.expected_complete_data)
        del expected['manufacturer']['id']
        del expected['manufacturer']['name']
        self.assertDictEqual(
            self.serialize(exclude={'manufacturer__id', 'manufacturer__name'}),
            expected
        )

    def test_exclude_single_child_field_many(self):
        expected = dict(self.expected_complete_data)
        del expected['skus'][0]['id']
        del expected['skus'][1]['id']
        self.assertDictEqual(self.serialize(exclude={'skus__id'}), expected)

    def test_exclude_multiple_child_fields_many(self):
        expected = dict(self.expected_complete_data)
        del expected['skus'][0]['id']
        del expected['skus'][0]['variant']
        del expected['skus'][1]['id']
        del expected['skus'][1]['variant']
        self.assertDictEqual(
            self.serialize(exclude={'skus__id', 'skus__variant'}),
            expected
        )

    def test_exclude_double_nested_field(self):
        expected = dict(self.expected_complete_data)
        del expected['skus'][0]['owners'][0]['email']
        self.assertDictEqual(
            self.serialize(exclude={'skus__owners__email'}),
            expected
        )

    def test_exclude_complex(self):
        expected = dict(self.expected_complete_data)
        del expected['name']
        del expected['manufacturer']['id']
        del expected['skus'][0]['variant']
        del expected['skus'][1]['variant']

        self.assertDictEqual(
            self.serialize(
                exclude={'name', 'manufacturer__id', 'skus__variant'}
            ),
            expected
        )

    def test_missing_root_field(self):
        with self.assertRaises(ValueError):
            self.serialize(exclude={'not_found'})

    def test_missing_child_field_foreign_key(self):
        with self.assertRaises(ValueError):
            self.serialize(exclude={'manufacturer__not_found'})

    def test_missing_child_key_many(self):
        with self.assertRaises(ValueError):
            self.serialize(exclude={'skus__not_found'})

    def test_field_ordering_unchanged_root(self):
        root_1 = self.serialize(exclude=('id', 'manufacturer'))
        root_2 = self.serialize(exclude=('manufacturer', 'id'))

        # The other of the fields is the same despite the `exclude` ordering
        self.assertEqual(root_1.keys(), root_2.keys())

        # And that order matches the serializer field ordering
        self.assertEqual(list(root_1.keys()), ['name', 'skus'])

    def test_field_ordering_unchanged_nested(self):
        child_1 = self.serialize(exclude=('skus__variant',))
        child_2 = self.serialize(exclude=('skus__owners',))

        keys_1 = child_1['skus'][0].keys()
        self.assertEqual(list(keys_1), ['id', 'owners'])

        keys_2 = child_2['skus'][0].keys()
        self.assertEqual(list(keys_2), ['id', 'variant'])
