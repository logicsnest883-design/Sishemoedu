from django.contrib import admin
from .models import Test, StudentScore, Attendance


# ==========================
# Test Admin
# ==========================
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):

    list_display = (
        "grade",
        "subject",
        "test_type",
        "term",
        "year",
        "test_date",
        "max_score",
    )

    list_filter = (
        "grade",
        "subject",
        "test_type",
        "term",
        "year",
    )

    search_fields = (
        "grade__name",
        "subject__name",
    )

    ordering = (
        "-year",
        "term",
        "grade",
        "subject__name",
    )


# ==========================
# Student Score Admin
# ==========================
@admin.register(StudentScore)
class StudentScoreAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "test",
        "score",
    )

    list_filter = (
        "test__grade",
        "test__subject",
        "test__test_type",
        "test__term",
        "test__year",
    )

    search_fields = (
        "student__first_name",
        "student__last_name",
        "test__subject__name",
    )

    ordering = (
        "test",
        "student",
    )


# ==========================
# Attendance Admin
# ==========================
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "year",
        "term",
        "week",
        "day",
        "status",
    )

    list_filter = (
        "year",
        "term",
        "week",
        "day",
        "status",
    )

    search_fields = (
        "student__first_name",
        "student__last_name",
    )

    ordering = (
        "-year",
        "term",
        "week",
        "day",
    )