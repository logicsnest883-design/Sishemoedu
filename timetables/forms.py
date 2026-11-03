from django import forms
from .models import Grade, Teacher, Subject, Timetable, TimetableEntry


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ["name", "lesson_duration", "is_active"]


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "is_active",
        ]


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "is_active"]


class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ["grade", "year", "term"]


class TimetableEntryForm(forms.ModelForm):
    class Meta:
        model = TimetableEntry
        fields = [
            "day",
            "start_time",
            "end_time",
            "activity",
            "subject",
            "teacher",
            "notes",
        ]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(is_active=True)
        self.fields["teacher"].queryset = Teacher.objects.filter(is_active=True)