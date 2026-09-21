from django.urls import include, path

urlpatterns = [
    path("api/v1/health/", include("apps.health.urls")),
    path("api/v1/", include("apps.agent.urls")),
]
