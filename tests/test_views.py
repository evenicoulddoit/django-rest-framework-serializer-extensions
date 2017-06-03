from __future__ import absolute_import

from django.http import QueryDict
from django.test import override_settings, RequestFactory, TestCase
from rest_framework.generics import RetrieveAPIView
from rest_framework.serializers import ModelSerializer
from test_plus.test import CBVTestCase

from rest_framework_serializer_extensions import utils, serializers, views
from tests import models


"""
START TEST VIEWS & SERIALIZERS
"""


class SkuTestSerializer(
    serializers.SerializerExtensionsMixin, ModelSerializer
):
    class Meta:
        model = models.Sku
        fields = ('id', 'variant')


class OrganizationTestSerializer(
    serializers.SerializerExtensionsMixin, ModelSerializer
):
    class Meta:
        model = models.Organization
        fields = ('id', 'name')


class OwnerTestSerializer(
    serializers.SerializerExtensionsMixin, ModelSerializer
):
    class Meta:
        model = models.Owner
        fields = ('id', 'name')
        expandable_fields = dict(
            organization=OrganizationTestSerializer,
            cars=dict(
                serializer=SkuTestSerializer,
                many=True
            )
        )


class APITestView(views.SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    queryset = models.Owner.objects.all()
    serializer_class = OwnerTestSerializer


"""
END TEST VIEWS & SERIALIZERS
"""


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

    def assertContextEquals(self, view_class, expected_context):
        view = self.get_instance(view_class)
        view.format_kwarg = 'json'
        view.request = self.request
        expected_context.update(
            request=self.request,
            view=view,
            format='json'
        )
        self.assertDictEqual(view.get_serializer_context(), expected_context)

    def test_no_attribute_field_names(self):
        self.assertContextEquals(
            APITestView,
            dict(
                expand=set(),
                expand_id_only=set(),
                exclude=set(),
                only=set()
            )
        )

    def test_attribute_field_names(self):
        class View(APITestView):
            extensions_expand = {'a', 'a1'}
            extensions_expand_id_only = {'b'}
            extensions_exclude = {'c'}
            extensions_only = {'d', 'd1', 'd2'}

        self.assertContextEquals(
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

        self.assertContextEquals(
            APITestView,
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

        self.assertContextEquals(
            APITestView,
            dict(
                expand={'a', 'a1'},
                expand_id_only={'b'},
                exclude={'c'},
                only={'d', 'd1', 'd2'}
            )
        )

    def test_query_params_override_attribute_field_names(self):
        class View(APITestView):
            extensions_expand = {'a', 'a1'}
            extensions_expand_id_only = {'b'}
            extensions_exclude = {'c'}
            extensions_only = {'d', 'd1', 'd2'}

        self.query_params.setlist('expand', ['override_a'])
        self.query_params.setlist('expand_id_only', ['override_b'])
        self.query_params.setlist('exclude', ['override_c'])
        self.query_params.setlist('only', ['override_d'])

        self.assertContextEquals(
            View,
            dict(
                expand={'override_a'},
                expand_id_only={'override_b'},
                exclude={'override_c'},
                only={'override_d'}
            )
        )

    def test_query_params_disabled_attribute(self):
        class View(APITestView):
            extensions_query_params_enabled = False
            extensions_expand = {'a', 'a1'}
            extensions_expand_id_only = {'b'}
            extensions_exclude = {'c'}
            extensions_only = {'d', 'd1', 'd2'}

        self.query_params.setlist('expand', ['override_a'])
        self.query_params.setlist('expand_id_only', ['override_b'])
        self.query_params.setlist('exclude', ['override_c'])
        self.query_params.setlist('only', ['override_d'])

        self.assertContextEquals(
            View,
            dict(
                expand={'a', 'a1'},
                expand_id_only={'b'},
                exclude={'c'},
                only={'d', 'd1', 'd2'}
            )
        )

    def test_query_params_disabled_method(self):
        class View(APITestView):
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

        self.assertContextEquals(
            View,
            dict(
                expand={'a', 'a1'},
                expand_id_only={'b'},
                exclude={'c'},
                only={'d', 'd1', 'd2'}
            )
        )

    def test_returns_empty_dict_when_no_request(self):
        self.request = None
        self.assertContextEquals(APITestView, dict())


class SerializerExtensionsAPIViewMixinTests(TestCase):
    """
    Functional tests to check that the serializer extensions work end-to-end.
    """
    fixtures = ['test_data.json']

    def setUp(self):
        self.owner = models.Owner.objects.get()
        self.organization = models.Organization.objects.get()
        self.sku_p100d = models.Sku.objects.get(variant='P100D')

    def get_response_data(self, **params):
        query_params = QueryDict(mutable=True)
        query_params.update(**params)
        request = RequestFactory().get('/')
        request.GET = query_params
        view = APITestView.as_view()
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
                    dict(variant=self.sku_p100d.variant)
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
        self.owner = models.Owner.objects.get()
        self.sku_p100d = models.Sku.objects.get(variant='P100D')

        class View(views.ExternalIdViewMixin, APITestView):
            pass

        self.view_class = View

    def get_response(self, pk):
        request = RequestFactory().get('/')
        view = self.view_class.as_view()
        return view(request, pk=pk)

    def test_matches_against_external_id(self):
        external_id = utils.external_id_from_model_and_internal_id(
            models.Owner, self.owner.pk
        )
        response = self.get_response(external_id)
        self.assertEquals(200, response.status_code)
        self.assertEquals(self.owner.pk, response.data['id'])

    def test_raises_404_when_not_found(self):
        bad_external_id = utils.external_id_from_model_and_internal_id(
            models.Sku, self.sku_p100d.pk
        )
        response = self.get_response(bad_external_id)
        self.assertEquals(404, response.status_code)
