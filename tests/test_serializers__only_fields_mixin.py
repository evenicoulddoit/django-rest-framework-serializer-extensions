from rest_framework import serializers

from rest_framework_serializer_extensions.serializers import OnlyFieldsMixin
from tests import models
from tests.base import SerializerMixinTestCase


"""
START TEST SERIALIZERS
"""


class OrganizationTestSerializer(OnlyFieldsMixin, serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name')
        model = models.Organization


class OwnerTestSerializer(OnlyFieldsMixin, serializers.ModelSerializer):
    organization = OrganizationTestSerializer()

    class Meta:
        fields = ('id', 'name', 'email', 'organization')
        model = models.Owner


class SkuTestSerializer(OnlyFieldsMixin, serializers.ModelSerializer):
    owners = OwnerTestSerializer(many=True)

    class Meta:
        fields = ('id', 'variant', 'owners')
        model = models.Sku


class ManufacturerTestSerializer(OnlyFieldsMixin, serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name')
        model = models.Manufacturer


class CarModelTestSerializer(OnlyFieldsMixin, serializers.ModelSerializer):
    skus = SkuTestSerializer(many=True)
    manufacturer = ManufacturerTestSerializer()

    class Meta:
        fields = ('id', 'name', 'skus', 'manufacturer')
        model = models.CarModel


"""
END TEST SERIALIZERS
"""


class OnlyFieldsSerializerMixinTests(SerializerMixinTestCase):
    """
    Functional tests for the OnlyFieldsSerializerMixin.

    By passing an "only" iterable to the serializer's context, the specified
    fields should be the only fields included during serialization.
    """
    def serialize(self, **context):
        """
        Return the serialized car with the given context applied
        """
        return (
            CarModelTestSerializer(self.carmodel_model_s, context=context)
            .data
        )

    def test_all_fields_implicit(self):
        self.assertDictEqual(self.serialize(), self.expected_complete_data)

    def test_all_fields_explicit(self):
        self.assertDictEqual(
            self.serialize(only=set()),
            self.expected_complete_data
        )

    def test_only_single_root_field(self):
        self.assertDictEqual(
            self.serialize(only={'id'}),
            dict(id=self.carmodel_model_s.pk)
        )

    def test_only_multiple_root_fields(self):
        self.assertDictEqual(
            self.serialize(only={'id', 'name'}),
            dict(
                id=self.carmodel_model_s.pk,
                name=self.carmodel_model_s.name
            )
        )

    def test_only_serializer_foreign_key_field(self):
        self.assertDictEqual(
            self.serialize(only={'manufacturer'}),
            dict(
                manufacturer=dict(
                    id=self.manufacturer_tesla.pk,
                    name=self.manufacturer_tesla.name,
                )
            )
        )

    def test_only_serializer_many_field(self):
        self.assertDictEqual(
            self.serialize(only={'skus'}),
            dict(
                skus=[
                    dict(
                        id=self.sku_p100d.pk,
                        variant=self.sku_p100d.variant,
                        owners=[
                            dict(
                                id=self.owner_tyrell.pk,
                                name=self.owner_tyrell.name,
                                email=self.owner_tyrell.email,
                                organization=dict(
                                    id=self.organization_ecorp.pk,
                                    name=self.organization_ecorp.name
                                )
                            ),
                        ]
                    ),
                    dict(
                        id=self.sku_70.pk,
                        variant=self.sku_70.variant,
                        owners=[]
                    )
                ]
            )
        )

    def test_only_single_child_field_foreign_key(self):
        self.assertDictEqual(
            self.serialize(only={'manufacturer__id'}),
            dict(
                manufacturer=dict(
                    id=self.manufacturer_tesla.pk
                )
            )
        )

    def test_only_multiple_child_fields_foreign_key(self):
        self.assertDictEqual(
            self.serialize(only={'manufacturer__id', 'manufacturer__name'}),
            dict(
                manufacturer=dict(
                    id=self.manufacturer_tesla.pk,
                    name=self.manufacturer_tesla.name
                )
            )
        )

    def test_only_single_child_field_many(self):
        self.assertDictEqual(
            self.serialize(only={'skus__id'}),
            dict(
                skus=[
                    dict(id=self.sku_p100d.pk),
                    dict(id=self.sku_70.pk),
                ]
            )
        )

    def test_only_multiple_child_fields_many(self):
        self.assertDictEqual(
            self.serialize(only={'skus__id', 'skus__variant'}),
            dict(
                skus=[
                    dict(
                        id=self.sku_p100d.pk,
                        variant=self.sku_p100d.variant
                    ),
                    dict(
                        id=self.sku_70.pk,
                        variant=self.sku_70.variant
                    )
                ]
            )
        )

    def test_double_nested_only(self):
        self.assertDictEqual(
            self.serialize(only={'skus__owners__name'}),
            dict(
                skus=[
                    dict(
                        owners=[
                            dict(name=self.owner_tyrell.name)
                        ]
                    ),
                    dict(owners=[]),
                ]
            )
        )

    def test_complex(self):
        self.assertDictEqual(
            self.serialize(
                only={'name', 'manufacturer__name', 'skus__variant'}
            ),
            dict(
                name=self.carmodel_model_s.name,
                manufacturer=dict(
                    name=self.manufacturer_tesla.name,
                ),
                skus=[
                    dict(variant=self.sku_p100d.variant),
                    dict(variant=self.sku_70.variant),
                ]
            )
        )

    def test_missing_root_field(self):
        with self.assertRaises(ValueError):
            self.serialize(only={'not_found'})

    def test_missing_child_field_foreign_key(self):
        with self.assertRaises(ValueError):
            self.serialize(only={'manufacturer__not_found'})

    def test_missing_child_key_many(self):
        with self.assertRaises(ValueError):
            self.serialize(only={'skus__not_found'})

    def test_error_serialize_all_and_specific(self):
        with self.assertRaises(ValueError):
            self.serialize(only={'manufacturer', 'manufacturer__name'})

    def test_field_ordering_unchanged_root(self):
        root_1 = self.serialize(only=('name', 'id', 'manufacturer'))
        root_2 = self.serialize(only=('manufacturer', 'id', 'name'))

        # The other of the fields is the same despite the `only` ordering
        self.assertEqual(root_1.keys(), root_2.keys())

        # And that order matches the serializer field ordering
        self.assertEqual(list(root_1.keys()), ['id', 'name', 'manufacturer'])

    def test_field_ordering_unchanged_nested(self):
        child_1 = self.serialize(only=('skus__variant', 'skus__owners'))
        child_2 = self.serialize(only=('skus__owners', 'skus__variant'))

        keys_1 = child_1['skus'][0].keys()
        keys_2 = child_2['skus'][0].keys()

        self.assertEqual(keys_1, keys_2)
        self.assertEqual(list(keys_1), ['variant', 'owners'])
