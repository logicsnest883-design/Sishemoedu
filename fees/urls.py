from django.urls import path
from . import views

app_name = "fees"

urlpatterns = [

    # Dashboard
    path(
        "",
        views.fees_dashboard,
        name="fees_dashboard"
    ),

    # Record payment for a student
    path(
        "record/<int:student_id>/",
        views.record_payment,
        name="record_payment"
    ),

    # View student payment history
    path(
        "student/<int:student_id>/",
        views.student_payments,
        name="student_payments"
    ),
    path(
    "students/<str:status>/",
    views.students_by_status,
    name="students_by_status"
),
    path(
    "update-balance/<int:student_id>/",
    views.update_balance,
    name="update_balance"
),


]
