from django.contrib import admin
from .models import Subject, Test, StudentScore


# ==========================
# Subject Admin
# ==========================
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "grade")
    list_filter = ("grade",)
    search_fields = ("name",)
    ordering = ("grade", "name")


# ==========================
# Test Admin
# ==========================
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("grade", "subject", "test_type", "test_date", "max_score")
    list_filter = ("grade", "subject", "test_type")
    search_fields = ("grade__name", "subject__name")
    ordering = ("-test_date",)


# ==========================
# Student Score Admin
# ==========================
@admin.register(StudentScore)
class StudentScoreAdmin(admin.ModelAdmin):
    list_display = ("student", "test", "score")
    list_filter = (
        "test__grade",
        "test__subject",
        "test__test_type",
    )
    search_fields = (
        "student__first_name",
        "student__last_name",
        "test__subject__name",
    )
    ordering = ("test", "student")




from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "week", "day", "status")  # columns to show
    list_filter = ("week", "day", "status")  # add filters for easy searching
    search_fields = ("student__first_name", "student__last_name")  # search by student name