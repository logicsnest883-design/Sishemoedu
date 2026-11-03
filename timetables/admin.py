
from django.contrib import admin
from .models import Grade, Teacher, Subject, Timetable, TimetableEntry


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("name", "lesson_duration", "is_active")
    list_filter = ("lesson_duration", "is_active")
    search_fields = ("name",)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "phone_number", "email", "is_active")
    list_filter = ("is_active",)
    search_fields = ("first_name", "last_name", "phone_number", "email")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


class TimetableEntryInline(admin.TabularInline):
    model = TimetableEntry
    extra = 1


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ("grade", "year", "term", "created_at")
    list_filter = ("year", "term", "grade")
    inlines = [TimetableEntryInline]


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = (
        "timetable", "day", "start_time", "end_time",
        "activity", "subject", "teacher"
    )
    list_filter = ("day", "activity", "timetable__year", "timetable__term")
