from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.events_list, name="events_list"),
    path("<slug:slug>/", views.event_detail, name="event_detail"),
    path("activity/<int:activity_id>/", views.activity_detail, name="activity_detail"),
]