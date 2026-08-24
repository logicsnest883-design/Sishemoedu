from django.urls import path
from . import views

urlpatterns = [
    path("", views.import_note, name="import_note"),
    path("save/", views.save_note, name="save_note"),
]