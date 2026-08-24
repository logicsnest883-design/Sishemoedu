from django.db import models
from accounts.models import UserProfile
from students.models import Grade, Student

# Subjects taught in school
class Subject(models.Model):
    name = models.CharField(max_length=50)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="subjects")

    def __str__(self):
        return f"{self.name} ({self.grade.name})"


# Types of tests
class TestType(models.TextChoices):
    FORTNIGHT_1 = "1st Fortnight Test", "1st Fortnight Test"
    MONTHLY_1 = "1st Monthly Test", "1st Monthly Test"
    MID_TERM = "Mid-Term Test", "Mid-Term Test"
    FORTNIGHT_2 = "2nd Fortnight Test", "2nd Fortnight Test"
    MONTHLY_2 = "2nd Monthly Test", "2nd Monthly Test"
    END_TERM = "End of Term Test", "End of Term Test"


# Test model
class Test(models.Model):

    TERM_CHOICES = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    ]

    grade = models.ForeignKey(
        Grade,
        on_delete=models.CASCADE,
        related_name="tests"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="tests"
    )

    test_type = models.CharField(
        max_length=50,
        choices=TestType.choices
    )

    term = models.CharField(
        max_length=10,
        choices=TERM_CHOICES,
        default="Term 1"
    )

    year = models.PositiveIntegerField(default=2026)

    test_date = models.DateField(auto_now_add=True)

    max_score = models.PositiveIntegerField(default=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "grade",
                    "subject",
                    "test_type",
                    "term",
                    "year",
                ],
                name="unique_test_per_period"
            )
        ]

    def __str__(self):
        return (
            f"{self.grade.name} - "
            f"{self.subject.name} - "
            f"{self.test_type} - "
            f"{self.term} - "
            f"{self.year}"
        )

    @property
    def teacher(self):
        return self.grade.teacher


# Score for each student
class StudentScore(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="scores")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="scores")
    score = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.test.test_type} - {self.score}"


from django.db import models
from students.models import Student


class Attendance(models.Model):

    STATUS_CHOICES = [
        ("P", "Present"),
        ("A", "Absent"),
    ]

    TERM_CHOICES = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    year = models.IntegerField(default=2026)

    term = models.CharField(
        max_length=10,
        choices=TERM_CHOICES,
        default="Term 1"
    )

    week = models.IntegerField()

    day = models.CharField(max_length=10)

    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "year", "term", "week", "day"],
                name="unique_student_attendance"
            )
        ]

        ordering = ["-year", "term", "week"]

    def __str__(self):
        return f"{self.student} - {self.term} {self.year} - Week {self.week} - {self.day}"