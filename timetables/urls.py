from django.urls import path
from . import views

app_name = "timetables"

urlpatterns = [
    path("", views.timetable_dashboard, name="dashboard"),

    path("grades/", views.grade_list, name="grade_list"),
    path("grades/add/", views.grade_create, name="grade_create"),
    path("grades/<int:pk>/edit/", views.grade_edit, name="grade_edit"),

    path("teachers/", views.teacher_list, name="teacher_list"),
    path("teachers/add/", views.teacher_create, name="teacher_create"),
    path("teachers/<int:pk>/edit/", views.teacher_edit, name="teacher_edit"),

    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/add/", views.subject_create, name="subject_create"),
    path("subjects/<int:pk>/edit/", views.subject_edit, name="subject_edit"),

    path("list/", views.timetable_list, name="timetable_list"),
    path("create/", views.timetable_create, name="timetable_create"),
    path("<int:pk>/", views.timetable_detail, name="timetable_detail"),
    path("<int:pk>/edit/", views.timetable_edit, name="timetable_edit"),
    path("<int:pk>/delete/", views.timetable_delete, name="timetable_delete"),

    path(
        "<int:timetable_pk>/entries/add/",
        views.entry_create,
        name="entry_create"
    ),
    path("entries/<int:pk>/edit/", views.entry_edit, name="entry_edit"),
    path("entries/<int:pk>/delete/", views.entry_delete, name="entry_delete"),
]