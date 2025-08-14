from django.urls import path

from .views import sortPageView, aboutPageView

urlpatterns = [
    path("about/", aboutPageView, name="about"),
    path("", sortPageView, name="home"),
]