import uuid

from django.db import models
from django.contrib.auth import get_user_model

from students.models import Student
from parents.models import Parent

User = get_user_model()


class Payment(models.Model):

    METHOD_CHOICES = [
        ("airtel", "Airtel Money"),
        ("bank", "Bank Transfer"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending Verification"),
        ("confirmed", "Confirmed"),
        ("rejected", "Rejected"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES
    )

    invoice_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True
    )

    proof_of_payment = models.FileField(
        upload_to="payment_proofs/",
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    payment_date = models.DateTimeField(
        auto_now_add=True
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_school_payments"
    )

    rejection_reason = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        if not self.invoice_number:
            self.invoice_number = (
                f"INV-{uuid.uuid4().hex[:10].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - K{self.amount}"