from django.urls import path

from . import views

urlpatterns = [
    path("api/greeting/", views.greeting),
    path("api/slow/", views.slow),
    path("health/", views.health),
]
