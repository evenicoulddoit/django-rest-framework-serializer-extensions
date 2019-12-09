import django
from django.db import connection
from django.http import QueryDict
from django.test import override_settings, RequestFactory
from mock import patch
from test_plus.test import CBVTestCase
from rest_framework.fields import SerializerMethodField

from tests import (
    models as test_models, serializers as test_serializers,
    views as test_views)


# TODO: Replace related set assignment with .set() when Django 1.10+ support


class QueryCounter(object):
    """
    A simple ContextManager to keep track of the number of DB queries made.
    """
    def __init__(self):
        self.count = 0

    def __enter__(self):
        self._start = len(connection.queries)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.count = len(connection.queries) - self._start
        self.queries = connection.queries[self._start:]

    def __str__(self):
        return "<QueryCounter: {}>".format(self.count)


query_counter = QueryCounter


# Debug exposes Django's queries
@override_settings(DEBUG=True)
class TestAutoOptimizedQueryset(CBVTestCase):
    """
    Fuctional tests for the automatic queryset optimization.

    Optimization should be performed based on the exact fields to be expanded.
    The view can be used to make additional select_related() calls.

    It cannot optimize queries made after expanding a many field.
    The serializer would have to update the queryset to make additional
    select related calls as required.

    Examples:

        SkuTestSerializer(expand=model)
            A `select_related()` call could optimize this.

        SkuTestSerializer(expand=model__manufacturer)
            As above. Nested `select_related()` calls should be possible.

        SkuTestSerializer(expand=owners)
            We need to make 2 DB calls no matter what in this case.
            A `prefetch_related()` would only provide optimization if the same
            collection was used multiple times during serialization.

        SkuTestSerializer(expand=owners__organization)
            As above, however the serializer which makes the `owners.all()`
            call could be optimized to call `select_related('organisation')`.

        SkuTestSerializer(expand=owners__cars)
            We could optimize this with a custom prefetch.
    """
    fixtures = ['test_data.json']

    def setUp(self):
        """
        Add more owners and skus to make the optimizations clearer.
        """
        self.carmodel_model_s = test_models.CarModel.objects.get()
        self.create_owners()
        self.create_skus()
        self.give_all_owners_all_skus()

    def create_skus(self):
        variants = ['80', '90d']

        for sku_variant in variants:
            test_models.Sku.objects.create(
                variant=sku_variant,
                model=self.carmodel_model_s
            )

    def create_owners(self):
        owners = [
            dict(name='Elliot Alderson', email='e.alderson@allsafe.com'),
            dict(name='Angela Moss', email='a.moss@allsafe.com'),
            dict(name='Gideon Goddard', email='g.goddard@allsafe.com'),
        ]

        allsafe = test_models.Organization.objects.create(name='Allsafe')

        for owner_details in owners:
            test_models.Owner.objects.create(
                preferences=test_models.OwnerPreferences.objects.create(),
                organization=allsafe,
                **owner_details
            )

    def give_all_owners_all_skus(self):
        skus = test_models.Sku.objects.all()

        for owner in test_models.Owner.objects.all():
            # TODO: Remove catch after dropping 1.8 support
            try:
                owner.cars.set(skus)
            except AttributeError:
                owner.cars = skus
                owner.save()

    def get_view_instance(self, view_class, **kwargs):
        view = self.get_instance(view_class, **kwargs)
        view.request = RequestFactory().get('/')
        view.request.query_params = QueryDict(mutable=True)
        view.format_kwarg = 'json'
        return view

    def get(self, view_class, optimize=True, **query_params):
        pk = view_class.queryset.first().pk

        with query_counter() as self.query_counter:
            view = self.get_view_instance(view_class, pk=pk)
            view.extensions_auto_optimize = optimize
            view.request.query_params.update(query_params)
            response = view.get(view.request)

        return response

    def assertNumQueries(
        self, view_class, expected_unoptimized, expected_optimized,
        **query_params
    ):
        """
        Assert that the expect view and parameters are optimized as expected.

        We get the results of the serializer when optimized and when not.
        Not only do we assert that the number of queries matches our
        expectations, but that both optimized and normal responses are equal.
        """
        response_unoptimized = self.get(
            view_class, optimize=False, **query_params
        )

        self.assertEqual(
            self.query_counter.count, expected_unoptimized,
            (
                "Expected {0} unoptimized queries, actually {1}."
                .format(expected_unoptimized, self.query_counter.count)
            )
        )
        response_optimized = self.get(view_class, **query_params)
        self.assertEqual(
            self.query_counter.count, expected_optimized,
            (
                "Expected {0} optimized queries, actually {1}."
                .format(expected_optimized, self.query_counter.count)
            )
        )

        self.assertEqual(
            response_optimized.data,
            response_unoptimized.data,
            "Optimized and unoptimized serialized results differed."
        )

    @patch.object(test_serializers.OwnerTestSerializer, 'auto_optimize')
    def test_auto_expand_disabled_by_default(self, mock_auto_optimize):
        view = self.get_view_instance(test_views.OwnerAPITestView)
        view.get_queryset()
        mock_auto_optimize.assert_not_called()

    @patch.object(test_serializers.OwnerTestSerializer, 'auto_optimize')
    def test_attribute_enabled_auto_optimization(self, mock_auto_optimize):
        """
        The extensions_auto_optimize view attribute determines optimization.
        """
        mock_auto_optimize.return_value = 'optimized'
        view = self.get_view_instance(test_views.OwnerAPITestView)
        view.extensions_auto_optimize = True
        queryset = view.get_queryset()
        mock_auto_optimize.assert_called_once()
        self.assertEqual('optimized', queryset)

    @patch.object(test_serializers.OwnerTestSerializer, 'auto_optimize')
    def test_method_enabled_auto_optimization(self, mock_auto_optimize):
        """
        The get_extensions_auto_optimize() view method determines optimization.
        """
        mock_auto_optimize.return_value = 'optimized'
        view = self.get_view_instance(test_views.OwnerAPITestView)
        view.get_extensions_auto_optimize = lambda: True
        queryset = view.get_queryset()
        mock_auto_optimize.assert_called_once()
        self.assertEqual('optimized', queryset)

    @override_settings(
        REST_FRAMEWORK=dict(
            SERIALIZER_EXTENSIONS=dict(
                AUTO_OPTIMIZE=True
            )
        )
    )
    @patch.object(test_serializers.OwnerTestSerializer, 'auto_optimize')
    def test_setting_enabled_auto_optimization(self, mock_auto_optimize):
        """
        The auto_optimize setting determines optimization globally.
        """
        mock_auto_optimize.return_value = 'optimized'
        view = self.get_view_instance(test_views.OwnerAPITestView)
        queryset = view.get_queryset()
        mock_auto_optimize.assert_called_once()
        self.assertEqual('optimized', queryset)

    def test_no_expansion(self):
        self.assertNumQueries(
            test_views.OwnerAPITestView,
            expected_unoptimized=1, expected_optimized=1
        )

    def test_expand_foreign_key(self):
        self.assertNumQueries(
            test_views.OwnerAPITestView,
            expected_unoptimized=2, expected_optimized=1,
            expand='organization'
        )

    def test_expand_many_relationship(self):
        self.assertNumQueries(
            test_views.OwnerAPITestView,
            expected_unoptimized=2, expected_optimized=2,
            expand='cars'
        )

    def test_expand_id_only_many_relationship(self):
        self.assertNumQueries(
            test_views.OwnerAPITestView,
            expected_unoptimized=2, expected_optimized=2,
            expand_id_only='cars'
        )

    def test_nested_expand_foreign_keys(self):
        self.assertNumQueries(
            test_views.SkuAPITestDetailView,
            expected_unoptimized=3, expected_optimized=1,
            expand='model__manufacturer'
        )

    def test_nested_expand_many_relationships(self):
        # Django <1.10 duplicated nested custom prefetches
        # https://code.djangoproject.com/ticket/25546
        expected_optimized = 3 if django.VERSION >= (1, 10) else 4

        self.assertNumQueries(
            test_views.ModelAPITestView,
            expected_unoptimized=6, expected_optimized=expected_optimized,
            expand='skus__owners'
        )

    def test_nested_expand_foreign_key_many_relationship(self):
        self.assertNumQueries(
            test_views.SkuAPITestDetailView,
            expected_unoptimized=3, expected_optimized=2,
            expand='model__skus'
        )

    def test_nested_expand_many_relationship_foreign_key(self):
        self.assertNumQueries(
            test_views.OwnerAPITestView,
            expected_unoptimized=6, expected_optimized=2,
            expand='cars__model'
        )

    def test_list_select_related(self):
        self.assertNumQueries(
            test_views.SkuAPITestListView,
            expected_unoptimized=5, expected_optimized=1,
            expand='model'
        )

    def test_list_prefetch_related(self):
        self.assertNumQueries(
            test_views.SkuAPITestListView,
            expected_unoptimized=5, expected_optimized=2,
            expand='owners'
        )

    def test_expand_self(self):
        """
        Expanding a serializer which sources self (*) does nothing.
        """
        self.assertNumQueries(
            test_views.OwnerAPITestView,
            expected_unoptimized=1, expected_optimized=1,
            expand='identity'
        )
        self.assertNumQueries(
            test_views.SkuAPITestDetailView,
            expected_unoptimized=2, expected_optimized=2,
            expand='owners__identity'
        )

    def test_expand_non_model_serializer_field(self):
        class Serializer(test_serializers.OwnerTestSerializer):
            class Meta(test_serializers.OwnerTestSerializer.Meta):
                expandable_fields = dict(
                    non_model=dict(
                        id_source=False,
                        id_model=False,
                        source='pk',  # Irrelevant existing attribute
                        serializer=test_serializers.NonModelTestSerializer
                    )
                )

        class View(test_views.OwnerAPITestView):
            serializer_class = Serializer

        self.assertNumQueries(
            View, expected_unoptimized=6, expected_optimized=2,
            expand='non_model__skus__model'
        )

    def test_expand_method_field_no_optimization(self):
        class Serializer(test_serializers.SkuTestSerializer):
            class Meta(test_serializers.SkuTestSerializer.Meta):
                expandable_fields = dict(
                    model=dict(
                        serializer=SerializerMethodField,
                        id_source=False
                    )
                )

            def get_model(self, obj):
                return self.represent_child(
                    name='model',
                    instance=obj.model,
                    serializer=test_serializers.ModelTestSerializer
                )

        class View(test_views.SkuAPITestDetailView):
            serializer_class = Serializer

        self.assertNumQueries(
            View, expected_unoptimized=2, expected_optimized=2, expand='model'
        )

    def test_expand_method_field_select_related(self):
        class Serializer(test_serializers.SkuTestSerializer):
            class Meta(test_serializers.SkuTestSerializer.Meta):
                expandable_fields = dict(
                    model=dict(
                        serializer=SerializerMethodField,
                        select_related=['model'],
                        id_source=False
                    )
                )

            def get_model(self, obj):
                return self.represent_child(
                    name='model',
                    instance=obj.model,
                    serializer=test_serializers.ModelTestSerializer
                )

        class View(test_views.SkuAPITestDetailView):
            serializer_class = Serializer

        self.assertNumQueries(
            View, expected_unoptimized=2, expected_optimized=1, expand='model'
        )

    def test_expand_method_field_prefetch_related(self):
        """
        Test that a method field can manually set a prefetch related.
        """
        class Serializer(test_serializers.ModelTestSerializer):
            class Meta(test_serializers.ModelTestSerializer.Meta):
                expandable_fields = dict(
                    skus=dict(
                        serializer=(
                            test_serializers.CustomPrefetchSkuSerializer
                        ),
                        many=True
                    )
                )

        class View(test_views.ModelAPITestView):
            serializer_class = Serializer

        # Django <1.10 duplicated nested custom prefetches
        # https://code.djangoproject.com/ticket/25546
        expected_optimized = 3 if django.VERSION >= (1, 10) else 4

        self.assertNumQueries(
            View,
            expected_unoptimized=6, expected_optimized=expected_optimized,
            expand='skus__owners'
        )

    def test_nested_expand_method_field_prefetch_related(self):
        """
        Test that further optimizations can be made after a method field.

        In this example, our owners method field returns a list of serialized
        owners with their organization details expanded.

        This is in a TODO/requires discussion state. We *could* optimize method
        field calls, but only if we have some idea of what the field is going
        to return. There are clearly large potential gains to be made here, but
        perhaps it's too difficult to automate.
        """
        class View(test_views.SkuAPITestListView):
            serializer_class = test_serializers.CustomPrefetchSkuSerializer

        # This could be 2 if optimized fully
        self.assertNumQueries(
            View, expected_unoptimized=21, expected_optimized=6,
            expand='owners__organization'
        )

    def test_auto_optimize_field_disabled(self):
        """
        Field definitions can be used to disable auto optimizations.
        """
        expandables = dict(
            test_serializers.OwnerTestSerializer.Meta.expandable_fields
        )
        expandables['organization'] = dict(
            serializer=test_serializers.OrganizationTestSerializer,
            auto_optimize=False
        )

        class TestSerializer(test_serializers.OwnerTestSerializer):
            class Meta(test_serializers.OwnerTestSerializer.Meta):
                expandable_fields = expandables

        class TestView(test_views.OwnerAPITestView):
            serializer_class = TestSerializer

        self.assertNumQueries(
            TestView, expected_unoptimized=2, expected_optimized=2,
            expand='organization'
        )

    def test_id_source_select_related_if_not_on_model(self):
        """
        A serializer with a custom ID source should select related.

        This is useful when serializing a OneToOne relationship, where the
        concrete FK reference is on the other model.
        """
        self.assertNumQueries(
            test_views.OwnerPreferencesAPITestView,
            expected_unoptimized=2, expected_optimized=1,
        )
