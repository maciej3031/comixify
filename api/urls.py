from django.conf.urls import url

from .views import Comixify


urlpatterns = [
    url(r'^$', Comixify.as_view(), name='annotate'),
]
