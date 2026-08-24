from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('student', 'Student'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)


    # Add fields later for teachers/parents/learners yes
    # Example:
    # phone = models.CharField(max_length=20, blank=True, null=True)
    # address = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
