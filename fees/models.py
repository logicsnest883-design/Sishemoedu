from django.db import models
from students.models import Student
from django.contrib.auth import get_user_model

User = get_user_model()

class Payment(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_date = models.DateTimeField(auto_now_add=True)

    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    reference = models.CharField(
        max_length=100,
        blank=True
    )

    def __str__(self):
        return f"{self.student} - {self.amount}"
