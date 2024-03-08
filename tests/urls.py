from django.urls import re_path
from django.views.generic import TemplateView

urlpatterns = [
    re_path(
        r"^models/(?P<external_id>\w+)/$",
        TemplateView.as_view(template_name="index.html"),
        name="car_model",
    ),
]
