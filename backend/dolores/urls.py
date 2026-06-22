# Third party imports
from django.contrib import admin
from django.urls import path

# Local imports.
from memories.api import api as memories_api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/memories/", memories_api.urls),
]
