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


from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from students.models import Student
from .models import Payment


@login_required
def parent_make_payment(request, student_id):

    parent = request.user.userprofile.parent_profile

    student = get_object_or_404(
        Student,
        id=student_id,
        parent=parent
    )

    payments = Payment.objects.filter(
        student=student,
        parent=parent
    ).order_by("-created_at")

    if request.method == "POST":

        method = request.POST.get("method", "").strip()

        try:
            fees = Decimal(request.POST.get("fees_amount", "0") or "0")
            transport = Decimal(request.POST.get("transport_amount", "0") or "0")
            lunch = Decimal(request.POST.get("lunch_amount", "0") or "0")
            uniform = Decimal(request.POST.get("uniform_amount", "0") or "0")
            other = Decimal(request.POST.get("other_amount", "0") or "0")

        except (ValueError, TypeError, InvalidOperation):

            messages.error(
                request,
                "Please enter valid amounts."
            )

            return render(
                request,
                "fees/parent_make_payment.html",
                {
                    "parent": parent,
                    "student": student,
                    "payments": payments,
                }
            )

        amounts = [fees, transport, lunch, uniform, other]

        if any(value < 0 for value in amounts):

            messages.error(
                request,
                "Payment amounts cannot be negative."
            )

            return render(
                request,
                "fees/parent_make_payment.html",
                {
                    "parent": parent,
                    "student": student,
                    "payments": payments,
                }
            )

        if other > 0:
            other_description = request.POST.get(
                "other_description",
                ""
            ).strip()

            if not other_description:

                messages.error(
                    request,
                    "Please specify what the other payment is for."
                )

                return render(
                    request,
                    "fees/parent_make_payment.html",
                    {
                        "parent": parent,
                        "student": student,
                        "payments": payments,
                    }
                )
        else:
            other_description = ""

        total_amount = (
            fees +
            transport +
            lunch +
            uniform +
            other
        )

        if total_amount <= 0:

            messages.error(
                request,
                "Please enter at least one payment amount."
            )

            return render(
                request,
                "fees/parent_make_payment.html",
                {
                    "parent": parent,
                    "student": student,
                    "payments": payments,
                }
            )

        if method not in ["airtel", "bank"]:

            messages.error(
                request,
                "Please select a payment method."
            )

            return render(
                request,
                "fees/parent_make_payment.html",
                {
                    "parent": parent,
                    "student": student,
                    "payments": payments,
                }
            )

        payment = Payment.objects.create(
            student=student,
            parent=parent,
            fees_amount=fees,
            transport_amount=transport,
            lunch_amount=lunch,
            uniform_amount=uniform,
            other_amount=other,
            other_description=other_description,
            amount=total_amount,
            method=method,
        )

        return redirect(
            "fees:parent_payment_invoice",
            payment_id=payment.id
        )

    return render(
        request,
        "fees/parent_make_payment.html",
        {
            "parent": parent,
            "student": student,
            "payments": payments,
        }
    )


@login_required
def parent_payment_invoice(request, payment_id):

    parent = request.user.userprofile.parent_profile

    payment = get_object_or_404(
        Payment,
        id=payment_id,
        parent=parent
    )

    if request.method == "POST":

        transaction_reference = request.POST.get(
            "transaction_reference",
            ""
        ).strip()

        proof_of_payment = request.FILES.get(
            "proof_of_payment"
        )

        if not transaction_reference:

            messages.error(
                request,
                "Please enter the transaction reference."
            )

            return render(
                request,
                "fees/parent_payment_invoice.html",
                {
                    "payment": payment,
                    "student": payment.student,
                }
            )

        if not proof_of_payment:

            messages.error(
                request,
                "Please upload your proof of payment."
            )

            return render(
                request,
                "fees/parent_payment_invoice.html",
                {
                    "payment": payment,
                    "student": payment.student,
                }
            )

        payment.transaction_reference = transaction_reference
        payment.proof_of_payment = proof_of_payment
        payment.status = "pending"

        payment.save()

        messages.success(
            request,
            "Your payment has been submitted for verification."
        )

        return redirect(
            "parents:parent_dashboard"
        )

    return render(
        request,
        "fees/parent_payment_invoice.html",
        {
            "payment": payment,
            "student": payment.student,
        }
    )