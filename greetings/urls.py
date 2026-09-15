from django.urls import path

from . import views

urlpatterns = [
    path("api/greeting/", views.greeting),
    path("health/", views.health),
]
