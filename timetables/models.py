
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class Grade(models.Model):
    LESSON_DURATION_CHOICES = [
        (30, "30 Minutes"),
        (40, "40 Minutes"),
    ]

    name = models.CharField(max_length=100, unique=True)
    lesson_duration = models.PositiveSmallIntegerField(
        choices=LESSON_DURATION_CHOICES,
        default=40
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Teacher(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Timetable(models.Model):
    TERM_CHOICES = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    ]

    grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        related_name="timetables"
    )
    year = models.PositiveIntegerField(
        validators=[
            MinValueValidator(2026),
            MaxValueValidator(4000)
        ]
    )
    term = models.CharField(max_length=10, choices=TERM_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "term", "grade__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["grade", "year", "term"],
                name="unique_grade_year_term_timetable"
            )
        ]

    def __str__(self):
        return f"{self.grade} - {self.term} - {self.year}"


class TimetableEntry(models.Model):
    DAY_CHOICES = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ]

    ACTIVITY_CHOICES = [
        ("lesson", "Lesson"),
        ("assembly", "Assembly"),
        ("devotion", "Devotion"),
        ("break", "Break"),
        ("lunch", "Lunch"),
        ("other", "Other Activity"),
    ]

    timetable = models.ForeignKey(
        Timetable,
        on_delete=models.CASCADE,
        related_name="entries"
    )

    day = models.CharField(max_length=10, choices=DAY_CHOICES)

    start_time = models.TimeField()
    end_time = models.TimeField()

    activity = models.CharField(
        max_length=20,
        choices=ACTIVITY_CHOICES,
        default="lesson"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="timetable_entries"
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="timetable_entries"
    )

    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["day", "start_time"]

    def clean(self):
        super().clean()

        errors = {}

        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                errors["end_time"] = "End time must be later than start time."

        if self.activity == "lesson":
            if not self.subject:
                errors["subject"] = "Please select a subject."

            if not self.teacher:
                errors["teacher"] = "Please select a teacher."

            if self.start_time and self.end_time and self.timetable_id:
                start = self.start_time.hour * 60 + self.start_time.minute
                end = self.end_time.hour * 60 + self.end_time.minute
                duration = end - start

                if duration != self.timetable.grade.lesson_duration:
                    errors["end_time"] = (
                        f"This grade requires "
                        f"{self.timetable.grade.lesson_duration}-minute lessons."
                    )

        elif self.subject_id or self.teacher_id:
            errors["activity"] = (
                "Only lessons can have a subject and teacher."
            )

        if (
            self.timetable_id
            and self.day
            and self.start_time
            and self.end_time
            and self.end_time > self.start_time
        ):
            grade_conflict = TimetableEntry.objects.filter(
                timetable__grade=self.timetable.grade,
                timetable__year=self.timetable.year,
                timetable__term=self.timetable.term,
                day=self.day,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).exclude(pk=self.pk)

            if grade_conflict.exists():
                errors["start_time"] = (
                    "This grade already has an activity during this period."
                )

            if self.teacher_id:
                teacher_conflict = TimetableEntry.objects.filter(
                    teacher=self.teacher,
                    timetable__year=self.timetable.year,
                    timetable__term=self.timetable.term,
                    day=self.day,
                    start_time__lt=self.end_time,
                    end_time__gt=self.start_time,
                ).exclude(pk=self.pk)

                if teacher_conflict.exists():
                    errors["teacher"] = (
                        "This teacher is already assigned to another class "
                        "during this period."
                    )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        if self.activity == "lesson":
            return (
                f"{self.timetable.grade} - {self.subject} - "
                f"{self.teacher} - {self.day}"
            )

        return f"{self.timetable.grade} - {self.get_activity_display()} - {self.day}"
