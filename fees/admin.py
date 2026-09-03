from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "student",
        "parent",
        "amount",
        "method",
        "status",
    )

    list_filter = (
        "status",
        "method",
    )

    search_fields = (
        "invoice_number",
        "transaction_reference",
    )