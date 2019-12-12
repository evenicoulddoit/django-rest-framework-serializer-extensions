from django.test import override_settings
from rest_framework import serializers

from rest_framework_serializer_extensions import utils
from rest_framework_serializer_extensions.serializers import (
    ExpandableFieldsMixin
)
from tests import models
from tests.base import SerializerMixinTestCase


"""
START TEST SERIALIZERS
"""
MODULE = 'tests.test_serializers__expandable_fields_mixin'


class ManufacturerTestSerializer(
    ExpandableFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        fields = ('id', 'name')
        model = models.Manufacturer
        expandable_fields = dict(
            models=dict(
                serializer='{0}.CarModelTestSerializer'.format(MODULE),
                many=True
            )
        )


class CarModelTestSerializer(
    ExpandableFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        fields = ('id', 'name')
        model = models.CarModel
        expandable_fields = dict(
            manufacturer=ManufacturerTestSerializer,
            skus=dict(
                serializer='{0}.SkuTestSerializer'.format(MODULE),
                many=True
            )
        )


class SkuTestSerializer(ExpandableFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Sku
        fields = ('id', 'variant')
        expandable_fields = dict(
            model=CarModelTestSerializer,
            owners=dict(
                serializer='{0}.OwnerTestSerializer'.format(MODULE),
                many=True,
            )
        )


class OrganizationTestSerializer(
    ExpandableFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        fields = ('id', 'name')
        model = models.Organization


class OwnerIdentityTestSerializer(
    ExpandableFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = models.Owner
        fields = ('email',)


class OwnerTestSerializer(ExpandableFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Owner
        fields = ('id', 'name')
        expandable_fields = dict(
            identities=dict(
                serializer=OwnerIdentityTestSerializer,
                source='*',
                id_source=False
            ),
            organization='{0}.OrganizationTestSerializer'.format(MODULE),
            cars=dict(
                serializer=SkuTestSerializer,
                many=True
            )
        )


class OwnerWithCarsTestSerializer(
    ExpandableFieldsMixin, serializers.ModelSerializer
):
    cars = SkuTestSerializer(many=True)

    class Meta:
        model = models.Owner
        fields = ('id', 'name', 'cars')


class OwnerWithMethodFieldTestSerializer(
    ExpandableFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = models.Owner
        fields = ('id', 'name')
        expandable_fields = dict(
            cars=serializers.SerializerMethodField
        )

    def get_cars(self, obj):
        return [sku.variant for sku in obj.cars.all()]


class OwnerWithCustomIdSourceTestSerializer(
    ExpandableFieldsMixin, serializers.ModelSerializer
):
    """
    Test serializer using an expanded field with a customer ID source.

    This can be useful for serializing non-Django model instances, or
    instances which have a reverse ForeignKey (i.e. the ForeignKey row is
    stored on the related model's table).
    """
    class Meta:
        model = models.Owner
        fields = ('id', 'name')
        expandable_fields = dict(
            organization=dict(
                serializer=OrganizationTestSerializer,
                id_source='organization.pk'
            )
        )


class CarModelWithWritableManufacturerTestSerializer(
    ExpandableFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        fields = ('id', 'name')
        model = models.CarModel
        expandable_fields = dict(
            manufacturer=dict(
                serializer=ManufacturerTestSerializer,
                read_only=False
            ),
        )


class NonModelTestSerializer(ExpandableFieldsMixin, serializers.Serializer):
    is_model = serializers.SerializerMethodField()

    def get_is_model(self, obj):
        return False

    def get_sku(self, obj):
        sku = models.Sku.objects.get(variant='P100D')
        serializer = SkuTestSerializer(instance=sku, context=self.context)
        serializer.bind('sku', self)
        return serializer.data

    class Meta:
        expandable_fields = dict(
            non_model=dict(
                serializer='{0}.NonModelTestSerializer'.format(MODULE),
                source='*',
                id_source=False
            ),
            sku=serializers.SerializerMethodField
        )


"""
END TEST SERIALIZERS
"""


class ExpandableFieldsSerializerMixinTests(SerializerMixinTestCase):
    """
    Functional tests for the ExpandableFieldsMixin.

    The mixin should allow complex, deferred fields, to be serialized only
    when required.
    """
    def serialize(self, **context):
        """
        Return the serialized car with the given context applied
        """
        return (
            OwnerTestSerializer(self.owner_tyrell, context=context)
            .data
        )

    def expand_instance_id(self, instance):
        return instance.pk

    def test_no_expansion(self):
        """
        Test when nothing is passed to the serializer, nothing is expanded.

        Because organization is a ForeignKey on the Owner model, its ID is
        always serialized.
        """
        self.assertDictEqual(
            self.serialize(),
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                )
            )
        )

    def test_expand_foreign_key(self):
        """
        Test that expanding a ForeignKey works as expected.

        Both the ID field and the full serialized instance should be included.
        """
        self.assertDictEqual(
            self.serialize(expand={'organization'}),
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                organization=dict(
                    id=self.organization_ecorp.pk,
                    name=self.organization_ecorp.name
                )
            )
        )

    def test_full_expand_one_to_many_key(self):
        """
        Test that fully expanding a OneToMany relation works as expected.
        """
        self.assertDictEqual(
            self.serialize(expand={'cars'}),
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                cars=[
                    dict(
                        id=self.sku_p100d.pk,
                        variant=self.sku_p100d.variant,
                        model_id=self.expand_instance_id(self.carmodel_model_s)
                    )
                ]
            )
        )

    def test_id_only_expand_one_to_many_key(self):
        """
        Test that ID-only expanding a OneToMany relation works as expected.

        This can be used to significantly reduce the payload when multiple
        identical instances are expected to be returned.
        """
        self.assertDictEqual(
            self.serialize(expand_id_only={'cars'}),
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                cars=[self.expand_instance_id(self.sku_p100d)],
            )
        )

    def test_expand_further_info_serializer(self):
        """
        Test that a generic "more information" serializer can be expanded.

        Here the source points to the same instance, and the ID source is
        the boolean False, which tells the serializer explictly to exclude
        the ID field.
        """
        self.assertDictEqual(
            self.serialize(expand={'identities'}),
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                identities=dict(
                    email=self.owner_tyrell.email
                )
            )
        )

    def test_multiple_expansion(self):
        """
        Test that expanding multiple fields works as expected.
        """
        self.assertDictEqual(
            self.serialize(expand={'identities', 'organization', 'cars'}),
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                identities=dict(
                    email=self.owner_tyrell.email
                ),
                organization=dict(
                    id=self.organization_ecorp.pk,
                    name=self.organization_ecorp.name
                ),
                cars=[
                    dict(
                        id=self.sku_p100d.pk,
                        variant=self.sku_p100d.variant,
                        model_id=self.expand_instance_id(
                            self.carmodel_model_s
                        )
                    )
                ],
            )
        )

    def test_nested_expansion(self):
        """
        Test that nested expansion works as expected.
        """
        self.assertDictEqual(
            self.serialize(expand={'cars__model__manufacturer'}),
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                cars=[
                    dict(
                        id=self.sku_p100d.pk,
                        variant=self.sku_p100d.variant,
                        model_id=self.expand_instance_id(
                            self.carmodel_model_s
                        ),
                        model=dict(
                            id=self.carmodel_model_s.pk,
                            name=self.carmodel_model_s.name,
                            manufacturer_id=self.expand_instance_id(
                                self.manufacturer_tesla
                            ),
                            manufacturer=dict(
                                id=self.manufacturer_tesla.pk,
                                name=self.manufacturer_tesla.name
                            )
                        )
                    )
                ]
            )
        )

    def test_nested_expansion_with_standard_fields(self):
        """
        The nested syntax works for standard fields too.

        In this test, a different serializer is used which always has an
        expanded representation of the owner's cars. This test asserts that,
        even though the "cars" field will always be present, it is accepted
        by the mixin in order to expand the child serializer's "model" field.
        """
        serialized = OwnerWithCarsTestSerializer(
            self.owner_tyrell, context=dict(expand={'cars__model'})
        )

        self.assertDictEqual(
            serialized.data,
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                cars=[
                    dict(
                        id=self.sku_p100d.pk,
                        variant=self.sku_p100d.variant,
                        model_id=self.expand_instance_id(
                            self.carmodel_model_s
                        ),
                        model=dict(
                            id=self.carmodel_model_s.pk,
                            name=self.carmodel_model_s.name,
                            manufacturer_id=self.expand_instance_id(
                                self.manufacturer_tesla
                            ),
                        )
                    )
                ]
            )
        )

    def test_custom_id_source_unexpanded(self):
        """
        Providing a custom 'id_source' should work as expected.
        """
        self.assertDictEqual(
            OwnerWithCustomIdSourceTestSerializer(self.owner_tyrell).data,
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                )
            )
        )

    def test_custom_id_source_expanded(self):
        """
        Providing a custom 'id_source' should not affect expansion
        """
        serialized = OwnerWithCustomIdSourceTestSerializer(
            self.owner_tyrell, context=dict(expand={'organization'})
        ).data

        self.assertDictEqual(
            serialized,
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                organization=dict(
                    id=self.organization_ecorp.pk,
                    name=self.organization_ecorp.name
                )
            )
        )

    def test_method_field_serializer_unexpanded(self):
        """
        Unexpanded SerializerMethodFields never have an ID source.
        """
        self.assertDictEqual(
            OwnerWithMethodFieldTestSerializer(self.owner_tyrell).data,
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
            )
        )

    def test_method_field_serializer_expanded(self):
        """
        Unexpanded SerializerMethodFields never have an ID source.
        """
        serialized = OwnerWithMethodFieldTestSerializer(
            self.owner_tyrell, context=dict(expand={'cars'})
        ).data

        self.assertDictEqual(
            serialized,
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                cars=[self.sku_p100d.variant]
            )
        )

    def test_custom_id_field(self):
        """
        Methods can be provided to generate custom ID fields.

        A SerializerMethodField is passed with the object as it's source.
        """
        class CustomIdSerializer(OwnerTestSerializer):
            def get_organization_id(self, owner):
                return "{0}-{1}".format(owner.name, owner.organization.name)

        serialized = CustomIdSerializer(self.owner_tyrell).data
        self.assertDictEqual(
            serialized,
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id="{0}-{1}".format(
                    self.owner_tyrell.name, self.organization_ecorp.name
                )
            )
        )

    def test_custom_id_only_field(self):
        """
        Methods can be provided to generate custom ID fields.

        A SerializerMethodField is passed with the object as it's source.
        """
        class CustomIdSerializer(OwnerTestSerializer):
            def get_cars_id_only(self, owner):
                return [car.variant for car in owner.cars.all()]

        serialized = CustomIdSerializer(
            self.owner_tyrell,
            context=dict(expand_id_only={'cars'})
        ).data

        self.assertDictEqual(
            serialized,
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                cars=[self.sku_p100d.variant]
            )
        )

    def test_custom_source_id_only_field(self):
        """
        A custom source can be used for id_only field expansion.

        A SerializerMethodField is passed with the object as it's source.
        """
        class CustomIdSourceSerializer(OwnerTestSerializer):
            class Meta(OwnerTestSerializer.Meta):
                expandable_fields = dict(
                    car_skus=dict(
                        serializer=SkuTestSerializer,
                        many=True,
                        source='cars'
                    )
                )

        serialized = CustomIdSourceSerializer(
            self.owner_tyrell,
            context=dict(expand_id_only={'car_skus'})
        ).data

        self.assertDictEqual(
            serialized,
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                car_skus=[self.expand_instance_id(self.sku_p100d)]
            )
        )

    def test_nested_id_only_expansion(self):
        """
        Nested ID expansion implies full expansion until the last node.
        """
        self.assertDictEqual(
            self.serialize(expand_id_only={'cars__model__skus'}),
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                cars=[
                    dict(
                        id=self.sku_p100d.pk,
                        variant=self.sku_p100d.variant,
                        model_id=self.expand_instance_id(
                            self.carmodel_model_s
                        ),
                        model=dict(
                            id=self.carmodel_model_s.pk,
                            name=self.carmodel_model_s.name,
                            manufacturer_id=self.expand_instance_id(
                                self.manufacturer_tesla
                            ),
                            skus=[
                                self.expand_instance_id(self.sku_p100d),
                                self.expand_instance_id(self.sku_70)
                            ]
                        )
                    )
                ]
            )
        )

    def test_exceed_default_max_depth(self):
        """
        Test that a max expansion depth of 3 is set on the serializer.
        """
        with self.assertRaises(ValueError):
            self.serialize(expand={'cars__model__manufacturer__models'})

    @override_settings(
        REST_FRAMEWORK=dict(
            SERIALIZER_EXTENSIONS=dict(
                MAX_EXPAND_DEPTH=4
            )
        )
    )
    def test_max_depth_setting_below_value(self):
        """
        Test that the MAX_EXPAND_DEPTH setting allows expansion as expected.
        """
        self.serialize(expand={'cars__model__manufacturer__models'})

    @override_settings(
        REST_FRAMEWORK=dict(
            SERIALIZER_EXTENSIONS=dict(
                MAX_EXPAND_DEPTH=2
            )
        )
    )
    def test_max_depth_setting_above_value(self):
        """
        Test that the MAX_EXPAND_DEPTH setting prevents expansion as expected.
        """
        with self.assertRaises(ValueError):
            self.serialize(expand={'cars__model__manufacturer__models'})

    def test_one_to_one_field_id_only_expansion(self):
        """
        Attempting to expand a *-to-one field by it's ID only should fail.
        """
        with self.assertRaises(ValueError):
            self.serialize(expand_id_only={'organization'})

    def test_unmatched_root_field_not_expandable(self):
        with self.assertRaises(ValueError):
            self.serialize(expand={'not_found'})

    def test_unmatched_nested_field_not_expandable(self):
        with self.assertRaises(ValueError):
            self.serialize(expand={'organization__not_found'})

    def test_unmatched_root_field_not_id_expandable(self):
        with self.assertRaises(ValueError):
            self.serialize(expand_id_only={'not_found'})

    def test_unmatched_nested_field_not_id_expandable(self):
        with self.assertRaises(ValueError):
            self.serialize(expand_id_only={'organization__not_found'})

    def test_can_ignore_matching_validation_through_context(self):
        self.assertDictEqual(
            self.serialize(
                expand={'organization', 'not_found'},
                validate_expand_instructions=False
            ),
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                organization=dict(
                    id=self.organization_ecorp.pk,
                    name=self.organization_ecorp.name
                )
            )
        )

    def test_can_ignore_matching_validation_through_meta(self):
        class IgnoreSerializer(OwnerTestSerializer):
            class Meta(OwnerTestSerializer.Meta):
                validate_expand_instructions = False

        serialized = IgnoreSerializer(
            self.owner_tyrell,
            context=dict(expand={'organization', 'not_found'})
        ).data

        self.assertDictEqual(
            serialized,
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                organization=dict(
                    id=self.organization_ecorp.pk,
                    name=self.organization_ecorp.name
                )
            )
        )

    def test_can_ignore_matching_validation_through_method(self):
        class IgnoreSerializer(OwnerTestSerializer):
            def get_validate_expand_instructions(self):
                return False

        serialized = IgnoreSerializer(
            self.owner_tyrell,
            context=dict(expand={'organization', 'not_found'})
        ).data

        self.assertDictEqual(
            serialized,
            dict(
                id=self.owner_tyrell.pk,
                name=self.owner_tyrell.name,
                organization_id=self.expand_instance_id(
                    self.organization_ecorp
                ),
                organization=dict(
                    id=self.organization_ecorp.pk,
                    name=self.organization_ecorp.name
                )
            )
        )

    def test_deserialize_read_only_id_field(self):
        """
        ID field for expandable field is not writable by default
        """
        serializer = CarModelTestSerializer(
            data=dict(
                name='Ka',
                manufacturer_id=(
                    self.expand_instance_id(self.manufacturer_tesla)
                )
            )
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(dict(name='Ka'), serializer.validated_data)

    def test_deserialize_writable_field(self):
        """
        If expandable relation is writable, values for ID resolved to instances
        """
        serializer = CarModelWithWritableManufacturerTestSerializer(
            data=dict(
                name='Ka',
                manufacturer_id=(
                    self.expand_instance_id(self.manufacturer_tesla)
                )
            )
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            dict(
                name='Ka',
                manufacturer_id=self.manufacturer_tesla.pk,
                manufacturer_id_resolved=self.manufacturer_tesla,
            ),
            serializer.validated_data
        )

    def test_writable_field_required(self):
        """
        If a field is writable, it can be required when deserializing.
        """
        serializer = CarModelWithWritableManufacturerTestSerializer(
            data=dict(name='Ka')
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue('manufacturer_id' in serializer.errors)

    def test_read_only_field_not_required(self):
        """
        If a field is read only, it is not required when deserializing.
        """
        serializer = CarModelTestSerializer(data=dict(name='Ka'))
        self.assertTrue(serializer.is_valid())

    def test_unexpanded_non_model_serializer(self):
        """
        Non-model serializers should support the mixin.
        """
        serializer = NonModelTestSerializer({})
        self.assertDictEqual(serializer.data, dict(is_model=False))

    def test_expanded_non_model_serializer_with_non_model_serializer(self):
        """
        Non-model to non-model expansion should work as expected.
        """
        serializer = NonModelTestSerializer(
            {}, context=dict(expand={'non_model'})
        )
        self.assertDictEqual(
            serializer.data,
            dict(
                is_model=False,
                non_model=dict(
                    is_model=False
                )
            )
        )

    def test_expanded_non_model_serializer_with_model_serializer(self):
        """
        Non-model to model expansion should work as expected.
        """
        serializer = NonModelTestSerializer(
            {}, context=dict(expand={'sku'})
        )
        self.assertDictEqual(
            serializer.data,
            dict(
                is_model=False,
                sku=dict(
                    id=self.sku_p100d.pk,
                    variant=self.sku_p100d.variant,
                    model_id=self.expand_instance_id(self.carmodel_model_s)
                )
            )
        )


@override_settings(
    REST_FRAMEWORK=dict(
        SERIALIZER_EXTENSIONS=dict(
            USE_HASH_IDS=True,
            HASH_IDS_SOURCE='tests.base.TEST_HASH_IDS'
        )
    )
)
class HashidsExpandableFieldsSerializerMixinTests(
    ExpandableFieldsSerializerMixinTests
):
    """
    Functional tests for the ExpandableFieldsSerializerMixin using HashIds.

    Uses the same test cases as before, but expected HashIds to be used
    whenever the mixin has expanded fields.
    """
    def expand_instance_id(self, instance):
        return utils.external_id_from_model_and_internal_id(
            type(instance), instance.pk
        )
