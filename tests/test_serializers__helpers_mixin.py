from django.test import TestCase
from rest_framework import serializers

from rest_framework_serializer_extensions.serializers import (
    SerializerHelpersMixin
)
from tests import models


"""
START TEST SERIALIZERS
"""


class OrganizationTestSerializer(
    SerializerHelpersMixin, serializers.ModelSerializer
):
    class Meta:
        fields = ('id', 'name')
        model = models.Organization


class OwnerTestSerializer(SerializerHelpersMixin, serializers.ModelSerializer):
    organization = OrganizationTestSerializer()

    class Meta:
        fields = ('id', 'name', 'email', 'organization')
        model = models.Owner


class SkuTestSerializer(SerializerHelpersMixin, serializers.ModelSerializer):
    owners = OwnerTestSerializer(many=True)

    class Meta:
        fields = ('id', 'variant', 'owners')
        model = models.Sku


class ManufacturerTestSerializer(
    SerializerHelpersMixin, serializers.ModelSerializer
):
    class Meta:
        fields = ('id', 'name')
        model = models.Manufacturer


class CarModelTestSerializer(
    SerializerHelpersMixin, serializers.ModelSerializer
):
    skus = SkuTestSerializer(many=True)
    manufacturer = ManufacturerTestSerializer()

    class Meta:
        fields = ('id', 'name', 'skus', 'manufacturer')
        model = models.CarModel


class CalculatedChildTestSerializer(
    SerializerHelpersMixin, serializers.Serializer
):
    id = serializers.IntegerField()
    hierarchy = serializers.SerializerMethodField()
    context_label = serializers.SerializerMethodField()

    def get_hierarchy(self, obj):
        return self.hierarchy

    def get_context_label(self, obj):
        return self.context.get('label')


class CalculatedParentTestSerializer(
    SerializerHelpersMixin, serializers.Serializer
):
    child = serializers.SerializerMethodField()

    def get_child(self, obj):
        return self.represent_child(
            name='child',
            serializer=CalculatedChildTestSerializer,
            instance=obj['child']
        )


"""
END TEST SERIALIZERS
"""


class SerializerHelpersHierarchyTests(TestCase):
    """
    Unit tests for the SerializerHelpersMixin's hierarchy cached property.

    The hierarchy forms the basis for including, excluding and extending
    fields using the other extension mixins.
    """
    def setUp(self):
        self.fields = CarModelTestSerializer().fields

    def test_hierarchy_root(self):
        self.assertEqual('', CarModelTestSerializer().hierarchy)

    def test_child_serializer(self):
        self.assertEqual(
            'manufacturer',
            self.fields['manufacturer'].hierarchy
        )

    def test_many_child_serializer(self):
        self.assertEqual(
            'skus',
            self.fields['skus'].child.hierarchy
        )

    def test_nested_child_serializer(self):
        self.assertEqual(
            'skus__owners',
            self.fields['skus'].child.fields['owners'].child.hierarchy
        )

    def test_double_nested_child_serializer(self):
        nested_serializer = (
            self.fields['skus']
            .child.fields['owners']
            .child.fields['organization']
        )

        self.assertEqual(
            'skus__owners__organization',
            nested_serializer.hierarchy
        )


class RepresentChildTests(TestCase):
    """
    Unit tests for the SerializerHelpersMixin's represent_child() method.

    The method allows a SerializerMethodField to easily call a child
    serializer whilst maintaining the hierarchy and context.
    """
    def setUp(self):
        self.internal_value = dict(child=dict(id=1))
        self.context = dict(label='Label')
        self.serializer = CalculatedParentTestSerializer(
            self.internal_value, context=self.context
        )
        self.serialized = self.serializer.data

    def test_hierarchy_maintained(self):
        self.assertEqual('child', self.serialized['child']['hierarchy'])

    def test_instance_passed(self):
        self.assertEqual(
            self.internal_value['child']['id'],
            self.serialized['child']['id']
        )

    def test_context_passed(self):
        self.assertEqual(
            self.context['label'],
            self.serialized['child']['context_label']
        )
