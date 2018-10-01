from django.urls import path

from .views import Comixify, ComixifyFromYoutube

urlpatterns = [
    path(r'', Comixify.as_view(), name='comixify'),
    path(r'from_yt/', ComixifyFromYoutube.as_view(), name='comixify_from_yt'),
]
