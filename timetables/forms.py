
from django import forms
from django.forms import formset_factory

from .models import (
    Grade,
    Teacher,
    Subject,
    OptionGroup,
    Timetable,
    TimetableEntry,
)


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


class OptionGroupForm(forms.ModelForm):
    class Meta:
        model = OptionGroup
        fields = ["grade", "name", "is_active"]


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
            "option_group",
            "classroom",
            "notes",
        ]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        timetable = kwargs.pop("timetable", None)

        super().__init__(*args, **kwargs)

        self.fields["subject"].queryset = Subject.objects.filter(
            is_active=True
        )

        self.fields["teacher"].queryset = Teacher.objects.filter(
            is_active=True
        )

        self.fields["option_group"].required = False

        if timetable:
            self.fields["option_group"].queryset = OptionGroup.objects.filter(
                grade=timetable.grade,
                is_active=True
            )
        elif self.instance and self.instance.pk:
            self.fields["option_group"].queryset = OptionGroup.objects.filter(
                grade=self.instance.timetable.grade,
                is_active=True
            )
        else:
            self.fields["option_group"].queryset = OptionGroup.objects.none()


TimetableEntryFormSet = formset_factory(
    TimetableEntryForm,
    extra=1,
    min_num=1,
    validate_min=True,
)
