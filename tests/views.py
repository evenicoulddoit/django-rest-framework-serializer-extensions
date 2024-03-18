"""
A collection of complete extensions views to be used by various tests.
"""

from rest_framework.generics import ListAPIView, RetrieveAPIView

from rest_framework_serializer_extensions.views import (
    SerializerExtensionsAPIViewMixin,
)
from tests import models as test_models, serializers as test_serializers


class OwnerAPITestView(SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    queryset = test_models.Owner.objects.all()
    serializer_class = test_serializers.OwnerTestSerializer


class OwnerPreferencesAPITestView(
    SerializerExtensionsAPIViewMixin, RetrieveAPIView
):
    queryset = test_models.OwnerPreferences.objects.all()
    serializer_class = test_serializers.OwnerPreferencesTestSerializer


class SkuAPITestDetailView(SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    queryset = test_models.Sku.objects.all()
    serializer_class = test_serializers.SkuTestSerializer


class SkuAPITestListView(SerializerExtensionsAPIViewMixin, ListAPIView):
    queryset = test_models.Sku.objects.all()
    serializer_class = test_serializers.SkuTestSerializer


class ModelAPITestView(SerializerExtensionsAPIViewMixin, RetrieveAPIView):
    queryset = test_models.CarModel.objects.all()
    serializer_class = test_serializers.ModelTestSerializer
