from django.http import QueryDict
from django.test import override_settings, RequestFactory, TestCase
from mock import patch
from test_plus.test import CBVTestCase

from rest_framework_serializer_extensions import (
    utils as extensions_utils, views as extensions_views)

from tests import models as test_models, views as test_views


class GetSerializerContextTests(CBVTestCase):
    """
    Unit tests for the mixins's get_serializer_context() method.

    This method should retrieve data from both the request's query parameters,
    and the view's attributes, to return the appropriate set of fields to
    include, exclude, and expand.
    """
    def setUp(self):
        self.query_params = QueryDict(mutable=True)
        self.request = RequestFactory().get('/')
        self.request.query_params = self.query_params

    def assertInContext(self, view_class, expected_context):
        view = self.get_instance(view_class)
        view.format_kwarg = 'json'
        view.request = self.request
        actual_context = {
            key: value
            for key, value in view.get_serializer_context().items()
            if key in expected_context
        }
        self.assertDictEqual(actual_context, expected_context)

    def test_no_attribute_field_names(self):
        self.assertInContext(
            test_views.OwnerAPITestView,
            dict(
                expand=set(),
                expand_id_only=set(),
                exclude=set(),
                only=set()
            )
        )

    def test_attribute_field_names(self):
        class View(test_views.OwnerAPITestView):
            extensions_expand = {'a', 'a1'}
            extensions_expand_id_only = {'b'}
            extensions_exclude = {'c'}
            extensions_only = {'d', 'd1', 'd2'}

        self.assertInContext(
            View,
            dict(
                expand={'a', 'a1'},
                expand_id_only={'b'},
                exclude={'c'},
                only={'d', 'd1', 'd2'}
            )
        )

    def test_query_params_list(self):
        self.query_params.setlist('expand', ['a', 'a1'])
        self.query_params.setlist('expand_id_only', ['b'])
        self.query_params.setlist('exclude', ['c'])
        self.query_params.setlist('only', ['d', 'd1', 'd2'])

        self.assertInContext(
            test_views.OwnerAPITestView,
            dict(
                expand={'a', 'a1'},
                expand_id_only={'b'},
                exclude={'c'},
                only={'d', 'd1', 'd2'}
            )
        )

    def test_query_params_comma_delimited(self):
        self.query_params.setlist('expand', ['a,a1'])
        self.query_params.setlist('expand_id_only', ['b'])
        self.query_params.setlist('exclude', ['c'])
        self.query_params.setlist('only', ['d,d1,d2'])

        self.assertInContext(
            test_views.OwnerAPITestView,
            dict(
                expand={'a', 'a1'},
                expand_id_only={'b'},
                exclude={'c'},
                only={'d', 'd1', 'd2'}
            )
        )

    def test_query_params_override_attribute_field_names(self):
        class View(test_views.OwnerAPITestView):
            extensions_expand = {'a', 'a1'}
            extensions_expand_id_only = {'b'}
            extensions_exclude = {'c'}
            extensions_only = {'d', 'd1', 'd2'}

        self.query_params.setlist('expand', ['override_a'])
        self.query_params.setlist('expand_id_only', ['override_b'])
        self.query_params.setlist('exclude', ['override_c'])
        self.query_params.setlist('only', ['override_d'])

        self.assertInContext(
            View,
            dict(
                expand={'override_a'},
                expand_id_only={'override_b'},
                exclude={'override_c'},
                only={'override_d'}
            )
        )

    def test_query_params_disabled_attribute(self):
        class View(test_views.OwnerAPITestView):
            extensions_query_params_enabled = False
            extensions_expand = {'a', 'a1'}
            extensions_expand_id_only = {'b'}
            extensions_exclude = {'c'}
            extensions_only = {'d', 'd1', 'd2'}

        self.query_params.setlist('expand', ['override_a'])
        self.query_params.setlist('expand_id_only', ['override_b'])
        self.query_params.setlist('exclude', ['override_c'])
        self.query_params.setlist('only', ['override_d'])

        self.assertInContext(
            View,
            dict(
                expand={'a', 'a1'},
                expand_id_only={'b'},
                exclude={'c'},
                only={'d', 'd1', 'd2'}
            )
        )

    def test_query_params_disabled_method(self):
        class View(test_views.OwnerAPITestView):
            extensions_expand = {'a', 'a1'}
            extensions_expand_id_only = {'b'}
            extensions_exclude = {'c'}
            extensions_only = {'d', 'd1', 'd2'}

            def get_extensions_query_params_enabled(self):
                return False

        self.query_params.setlist('expand', ['override_a'])
        self.query_params.setlist('expand_id_only', ['override_b'])
        self.query_params.setlist('exclude', ['override_c'])
        self.query_params.setlist('only', ['override_d'])

        self.assertInContext(
            View,
            dict(
                expand={'a', 'a1'},
                expand_id_only={'b'},
                exclude={'c'},
                only={'d', 'd1', 'd2'}
            )
        )

    @patch.object(
        extensions_views.SerializerExtensionsAPIViewMixin,
        'get_extensions_auto_optimize'
    )
    def test_auto_optimization_included(self, mock_get_auto_optimize):
        """
        The "auto_optimize" value is passed to the context correctly.
        """
        mock_get_auto_optimize.return_value = False
        self.assertInContext(
            test_views.OwnerAPITestView, dict(auto_optimize=False)
        )

        mock_get_auto_optimize.return_value = True
        self.assertInContext(
            test_views.OwnerAPITestView, dict(auto_optimize=True)
        )


class SerializerExtensionsAPIViewMixinTests(TestCase):
    """
    Functional tests to check that the serializer extensions work end-to-end.
    """
    fixtures = ['test_data.json']

    def setUp(self):
        self.owner = test_models.Owner.objects.get()
        self.organization = test_models.Organization.objects.get()
        self.sku_p100d = test_models.Sku.objects.get(variant='P100D')
        self.carmodel_model_s = test_models.CarModel.objects.get()

    def get_response_data(self, **params):
        query_params = QueryDict(mutable=True)
        query_params.update(**params)
        request = RequestFactory().get('/')
        request.GET = query_params
        view = test_views.OwnerAPITestView.as_view()
        return view(request, pk=self.owner.pk).data

    def test_no_modifications(self):
        data = self.get_response_data()
        self.assertDictEqual(
            data,
            dict(
                id=self.owner.pk,
                name=self.owner.name,
                organization_id=self.organization.pk
            )
        )

    def test_complex_serialization(self):
        data = self.get_response_data(
            expand='cars',
            only='cars',
            exclude='cars__id'
        )

        self.assertDictEqual(
            data,
            dict(
                cars=[
                    dict(
                        variant=self.sku_p100d.variant,
                        model_id=self.carmodel_model_s.pk
                    )
                ]
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
class ExternalIdViewMixinTests(TestCase):
    """
    Functional tests for the ExternalIdViewMixinTests.

    Applying the mixin to an APIView should allow the view to retrieve the
    instance based on it's external ID (using HashIds).
    """
    fixtures = ['test_data.json']

    def setUp(self):
        self.owner = test_models.Owner.objects.get()
        self.sku_p100d = test_models.Sku.objects.get(variant='P100D')

        class View(
            extensions_views.ExternalIdViewMixin, test_views.OwnerAPITestView
        ):
            pass

        self.view_class = View

    def get_response(self, pk):
        request = RequestFactory().get('/')
        view = self.view_class.as_view()
        return view(request, pk=pk)

    def test_matches_against_external_id(self):
        external_id = extensions_utils.external_id_from_model_and_internal_id(
            test_models.Owner, self.owner.pk
        )
        response = self.get_response(external_id)
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.owner.pk, response.data['id'])

    def test_raises_404_when_not_found(self):
        bad_external_id = (
            extensions_utils.external_id_from_model_and_internal_id(
                test_models.Sku, self.sku_p100d.pk
            )
        )
        response = self.get_response(bad_external_id)
        self.assertEqual(404, response.status_code)
