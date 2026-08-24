"""
URL configuration for SchoolLibrary project.
"""

from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path("", include("Core.urls")),
    path("", include("accounts.urls")),
    path("", include("students.urls")),
    path("parents/", include("parents.urls")),
    path("fees/", include("fees.urls")),
    path("", include("teachers.urls")),
    path('events/', include('events.urls')),
    path("games/", include("games.urls")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )