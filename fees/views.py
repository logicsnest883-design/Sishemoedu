from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from students.models import Student
from .models import Payment


from django.db.models import Sum
from students.models import Student
from .models import Payment


@login_required
def fees_dashboard(request):

    total_students = Student.objects.count()

    total_collected = Payment.objects.aggregate(
        total=Sum("amount")
    )["total"] or 0

    students_with_balance = Student.objects.filter(
        school_balance__gt=0
    ).count()

    settled_students = Student.objects.filter(
        school_balance=0
    ).count()

    overpaid_students = Student.objects.filter(
        school_balance__lt=0
    ).count()

    recent_payments = Payment.objects.select_related(
        "student", "student__profile"
    ).order_by("-payment_date")[:10]

    return render(
        request,
        "fees/dashboard.html",
        {
            "total_students": total_students,
            "total_collected": total_collected,
            "students_with_balance": students_with_balance,
            "settled_students": settled_students,
            "overpaid_students": overpaid_students,
            "recent_payments": recent_payments,
        }
    )

@login_required
def students_by_status(request, status):

    if status == "owing":
        students = Student.objects.filter(school_balance__gt=0)
        title = "Students With Balance"

    elif status == "settled":
        students = Student.objects.filter(school_balance=0)
        title = "Settled Students"

    elif status == "overpaid":
        students = Student.objects.filter(school_balance__lt=0)
        title = "Overpaid Students"

    else:
        students = Student.objects.all()
        title = "All Students"

    return render(
        request,
        "fees/students_by_status.html",
        {
            "students": students,
            "title": title,
        }
    )



from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal


@login_required
def record_payment(request, student_id):

    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        amount = Decimal(request.POST.get("amount"))
        reference = request.POST.get("reference")

        # Create payment
        Payment.objects.create(
            student=student,
            amount=amount,
            received_by=request.user,
            reference=reference
        )

        # Reduce balance
        student.school_balance -= amount
        student.save()

        messages.success(request, "Payment recorded successfully.")
        return redirect("fees:fees_dashboard")

    return render(
        request, "fees/record_payment.html", {"student": student})



@login_required
def student_payments(request, student_id):

    student = get_object_or_404(Student, id=student_id)

    payments = student.payments.all().order_by("-payment_date")

    return render(
        request,
        "fees/student_payments.html",
        {
            "student": student,
            "payments": payments,
        }
    )


from .forms import UpdateBalanceForm

@login_required
def update_balance(request, student_id):

    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        form = UpdateBalanceForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Balance updated successfully.")
            return redirect("fees:students_by_status", status="all")
    else:
        form = UpdateBalanceForm(instance=student)

    return render(
        request,
        "fees/update_balance.html",
        {
            "form": form,
            "student": student
        }
    )
