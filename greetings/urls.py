from django.urls import path

from . import views

urlpatterns = [
    path("api/greeting/", views.greeting),
    path("api/slow/", views.slow),
    path("api/long/", views.long_job_start),
    path("api/jobs/", views.jobs),
    path("health/", views.health),
]
