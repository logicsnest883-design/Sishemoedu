from django.urls import path
from . import views

app_name = "parents"

urlpatterns = [

    path("grades/", views.parent_grade_list, name="parent_grade_list"),

    path(
        "grades/<int:grade_id>/",
        views.parents_in_grade,
        name="parents_in_grade"
    ),

    path(
        "detail/<int:parent_id>/",
        views.parent_detail,
        name="parent_detail"
    ),
    path("create/", views.create_parent, name="create_parent"),
    path("parent/dashboard/", views.parent_dashboard, name="parent_dashboard"),
    path("child/<int:student_id>/", views.parent_child_detail, name="parent_child_detail"),

]
