from django.urls import path
from . import views

urlpatterns = [
    path("system-admin/login/", views.admin_login, name="admin_login"),
    path("system-admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("logout/", views.user_logout, name="logout"),
    path("teacher/login/", views.teacher_login, name="teacher_login"),
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("parent/login/", views.parent_login, name="parent_login"),
    path("admin/pending-payments/",
    views.pending_payments,
    name="pending_payments"
),

    path(
    "admin/payment/<int:payment_id>/",
    views.payment_verification_detail,
    name="payment_verification_detail"
),

    path(
    "admin/payment/<int:payment_id>/confirm/",
    views.confirm_payment,
    name="confirm_payment"
),

    path(
    "admin/payment/<int:payment_id>/reject/",
    views.reject_payment,
    name="reject_payment"
),
    path(
    "parent-access/",
    views.parent_access_control,
    name="parent_access_control"
),

    path(
    "parent-access/grade/<int:grade_id>/",
    views.parent_access_grade,
    name="parent_access_grade"
),

    path(
    "parent-access/<int:parent_id>/update/",
    views.update_parent_access,
    name="update_parent_access"
),
    path(
        "class-lists/",
        views.class_lists,
        name="class_lists"
),

    path(
        "class-lists/<int:grade_id>/",
        views.class_list_detail,
        name="class_list_detail"
),
    path("parent/dashboard/", views.parent_dashboard, name="parent_dashboard"),
    path(
    "school-admin-dashboard/",
    views.school_admin_dashboard,
    name="school_admin_dashboard"
),
    #path("parent/child/<int:student_id>/", views.parent_child_detail, name="parent_child_detail"),

    path(
    "parent/tests/<int:student_id>/<str:test_type>/",
    views.parent_test_detail,
    name="parent_test_detail"
),
]
