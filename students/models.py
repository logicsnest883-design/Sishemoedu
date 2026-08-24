from django.db import models
from accounts.models import UserProfile
from parents.models import Parent

from django.db import models
from accounts.models import UserProfile

class Grade(models.Model):
    name = models.CharField(max_length=50)

    teacher = models.OneToOneField(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'teacher'},
        related_name='assigned_grade'
    )

    def __str__(self):
        return self.name



class Student(models.Model):
    # Student User Account (optional)
    profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "student"},
        blank=True,
        null=True
    )

    # Personal Info
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    photo = models.ImageField(
        upload_to="students/photos/",
        blank=True,
        null=True
    )
    full_photo = models.ImageField(
        upload_to="students/full_photos/",
        blank=True,
        null=True
    )

    # Class / Grade
    grade = models.ForeignKey(
        Grade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Link to Parent model
    parent = models.ForeignKey(
        Parent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    # School Info
    school_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Transport & Lunch
    on_transport = models.BooleanField(default=False)
    on_school_lunch = models.BooleanField(default=False)

    # Physical & Personal Info
    height_cm = models.PositiveIntegerField(null=True, blank=True)
    nationality = models.CharField(max_length=100)
    tribe = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        # Use first and last name if profile is missing
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.profile and self.profile.user:
            return self.profile.user.get_full_name()
        return "Unnamed Student"
