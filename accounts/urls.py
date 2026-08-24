from django.urls import path
from . import views

urlpatterns = [
    path("system-admin/login/", views.admin_login, name="admin_login"),
    path("system-admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("logout/", views.user_logout, name="logout"),
    path("teacher/login/", views.teacher_login, name="teacher_login"),
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("parent/login/", views.parent_login, name="parent_login"),
    path("parent/dashboard/", views.parent_dashboard, name="parent_dashboard"),
    #path("parent/child/<int:student_id>/", views.parent_child_detail, name="parent_child_detail"),

    path(
    "parent/tests/<int:student_id>/<str:test_type>/",
    views.parent_test_detail,
    name="parent_test_detail"
),
]
