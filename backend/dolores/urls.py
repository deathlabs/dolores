# Third party imports
from django.contrib import admin
from django.urls import path

from checkpoints.api import api as checkpoints_api
from memories.api import api as memories_api

# Local imports.
from .healthcheck import api as health_api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/checkpoints/", checkpoints_api.urls),
    path("api/v1/healthcheck/", health_api.urls),
    path("api/v1/memories/", memories_api.urls),
]
