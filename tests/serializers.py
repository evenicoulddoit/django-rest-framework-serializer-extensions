"""
A collection of complete extensions serializers to be used by various tests.
"""

from rest_framework import serializers

from rest_framework_serializer_extensions.serializers import (
    ExtensionsModelSerializer,
    ExtensionsSerializer,
)
from tests import models as test_models


class ManufacturerTestSerializer(ExtensionsModelSerializer):
    class Meta:
        model = test_models.Owner
        fields = ("id", "name")


class ModelTestSerializer(ExtensionsModelSerializer):
    class Meta:
        model = test_models.CarModel
        fields = ("id", "name")
        expandable_fields = dict(
            manufacturer=ManufacturerTestSerializer,
            skus=dict(
                serializer="tests.serializers.SkuTestSerializer", many=True
            ),
        )


class SkuTestSerializer(ExtensionsModelSerializer):
    class Meta:
        model = test_models.Sku
        fields = ("id", "variant")
        expandable_fields = dict(
            owners=dict(
                serializer="tests.serializers.OwnerTestSerializer", many=True
            ),
            model=ModelTestSerializer,
            manufacturer=dict(
                serializer=ManufacturerTestSerializer,
                source="model.manufacturer",
                id_source=False,
            ),
        )


class OrganizationTestSerializer(ExtensionsModelSerializer):
    class Meta:
        model = test_models.Organization
        fields = ("id", "name")
        expandable_fields = dict(
            staff=dict(
                serializer="tests.serializers.OwnerTestSerializer", many=True
            ),
            cars=dict(serializer=SkuTestSerializer, many=True, source="cars"),
        )


class OwnerIdentityTestSerializer(ExtensionsModelSerializer):
    class Meta:
        model = test_models.Owner
        fields = ("email",)


class OwnerPreferencesTestSerializer(ExtensionsModelSerializer):
    class Meta:
        model = test_models.OwnerPreferences
        fields = ("price_limit_dollars",)
        expandable_fields = dict(
            owner=dict(
                serializer="tests.serializers.OwnerTestSerializer",
                id_source="owner.pk",
            ),
            favorite_manufacturer=(
                "tests.serializers.ManufacturerTestSerializer"
            ),
        )


class OwnerTestSerializer(ExtensionsModelSerializer):
    class Meta:
        model = test_models.Owner
        fields = ("id", "name")
        expandable_fields = dict(
            organization=OrganizationTestSerializer,
            cars=dict(serializer=SkuTestSerializer, many=True),
            identity=dict(
                serializer=OwnerIdentityTestSerializer,
                id_source=False,
                source="*",
            ),
        )


class CustomPrefetchSkuSerializer(SkuTestSerializer):
    class Meta(SkuTestSerializer):
        model = test_models.Sku
        fields = ("id", "variant")
        expandable_fields = dict(
            owners=dict(
                serializer=serializers.SerializerMethodField,
                id_source=False,
                prefetch_related=["owners"],
            )
        )

    def get_owners(self, obj):
        return self.represent_child(
            name="owners",
            instance=obj.owners.all(),
            serializer=OwnerTestSerializer,
            many=True,
        )


class NonModelTestSerializer(ExtensionsSerializer):
    foo = serializers.SerializerMethodField()

    class Meta:
        expandable_fields = dict(skus=serializers.SerializerMethodField)

    def get_foo(self, obj):
        return "foo"

    def get_skus(self, obj):
        return self.represent_child(
            name="skus",
            instance=test_models.Sku.objects.all(),
            serializer=SkuTestSerializer,
            many=True,
        )
