from django.conf.urls import url
from django.views.generic import TemplateView

urlpatterns = [
    url(
        r'^models/(?P<external_id>\w+)/$',
        TemplateView.as_view(template_name="index.html"),
        name='car_model'
    ),
]
