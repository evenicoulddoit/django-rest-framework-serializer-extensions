from django.http.request import QueryDict
from django.test.client import RequestFactory
from rest_framework import serializers
from rest_framework.generics import RetrieveAPIView
from test_plus.test import CBVTestCase

from rest_framework_serializer_extensions.serializers import (
    ExtensionsModelSerializer,
)
from rest_framework_serializer_extensions.views import (
    SerializerExtensionsAPIViewMixin,
)
from tests import models
from tests.base import SerializerMixinTestCase


class OrganizationTestSerializer(ExtensionsModelSerializer):
    foo = serializers.SerializerMethodField()
    zulu = serializers.SerializerMethodField()

    class Meta:
        model = models.Organization
        fields = ("id", "name", "foo", "zulu")

    def get_foo(self, _):
        return self.context["request"].query_params.get("foo")

    def get_zulu(self, _):
        return self.context["zulu"]


class OwnerTestSerializer(ExtensionsModelSerializer):
    class Meta:
        model = models.Owner
        fields = ("id", "name")
        expandable_fields = dict(organization=OrganizationTestSerializer,)


class OwnerAPITestView(SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    queryset = models.Owner.objects.all()
    serializer_class = OwnerTestSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(zulu=1)
        return context


class NestedContextTests(CBVTestCase, SerializerMixinTestCase):
    def test_expanded_serializer_receives_context(self):
        """Test the nested serializers have access to the context"""
        query_params = QueryDict(mutable=True)
        request = RequestFactory().get("/")
        request.query_params = query_params

        view = self.get_instance(OwnerAPITestView)
        view.format_kwarg = "json"
        view.request = request
        view.kwargs = dict(pk=self.owner_tyrell.pk)

        query_params.setlist("expand", ["organization"])
        query_params.update(foo="bar")
        response = view.get(request)

        # The foo value should be derived from the request's query params
        self.assertEqual("bar", response.data["organization"]["foo"])

        # The zulu value should be dervied from the view's context
        self.assertEqual(1, response.data["organization"]["zulu"])
