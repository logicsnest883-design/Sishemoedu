from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.decorators import user_passes_test

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # check if user has admin role
            try:
                profile = user.userprofile
                if profile.role == "admin":
                    login(request, user)
                    return redirect("admin_dashboard")
                else:
                    messages.error(request, "You are not allowed to access the admin portal.")
            except UserProfile.DoesNotExist:
                messages.error(request, "Profile not found. Contact system administrator.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/admin_login.html")

def admin_dashboard(request):
    # protect admin dashboard
    if not request.user.is_authenticated:
        return redirect("admin_login")

    try:
        if request.user.userprofile.role != "admin":
            return redirect("admin_login")
    except:
        return redirect("admin_login")

    return render(request, "accounts/admin_dashboard.html")


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from accounts.models import UserProfile

# -----------------------------
# TEACHER LOGIN
# -----------------------------
def teacher_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # check if user has teacher role
            try:
                profile = user.userprofile
                if profile.role == "teacher":
                    login(request, user)
                    return redirect("teacher_dashboard")
                else:
                    messages.error(request, "You are not allowed to access the teacher portal.")
            except UserProfile.DoesNotExist:
                messages.error(request, "Profile not found. Contact system administrator.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/teacher_login.html")


# -----------------------------
# TEACHER DASHBOARD
# -----------------------------
def teacher_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("teacher_login")

    try:
        if request.user.userprofile.role != "teacher":
            return redirect("teacher_login")
    except UserProfile.DoesNotExist:
        return redirect("teacher_login")

    # Example: you can pass teacher-specific data here
    # students in their classes, grades, etc.
    context = {
        "teacher_name": request.user.get_full_name(),
    }

    return render(request, "accounts/teacher_dashboard.html", context)



def parent_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                profile = user.userprofile

                if profile.role == "parent":
                    login(request, user)
                    return redirect("parent_dashboard")
                else:
                    messages.error(request, "You are not allowed to access the parent portal.")

            except UserProfile.DoesNotExist:
                messages.error(request, "Profile not found. Contact system administrator.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/parent_login.html")


from django.contrib.auth.decorators import login_required
from students.models import Student
from teachers.models import Attendance
from parents.models import Parent

from teachers.models import Test, StudentScore

@login_required
def parent_dashboard(request):
    profile = request.user.userprofile
    parent = profile.parent_profile

    children = Student.objects.filter(
        parent=parent
    ).select_related(
        "grade",
        "profile",
        "profile__user"
    )

    for child in children:

        # -------------------------
        # ATTENDANCE
        # -------------------------
        records = Attendance.objects.filter(student=child)

        total = records.count()
        present = records.filter(status="P").count()

        child.attendance_percentage = (
            round((present / total) * 100, 2)
            if total > 0
            else 0
        )

        # -------------------------
        # TESTS
        # -------------------------
        scores = (
            StudentScore.objects
            .filter(student=child)
            .select_related("test")
        )

        child.tests_by_type = {}

        for score in scores:
            test_type = score.test.test_type

            if test_type not in child.tests_by_type:
                child.tests_by_type[test_type] = []

            child.tests_by_type[test_type].append(score)

        # -------------------------
        # RESULTS ACCESS
        # -------------------------
        if child.school_balance <= 0:
            # No outstanding balance
            child.can_view_results = True

        else:
            # Outstanding balance - check admin approval
            child.can_view_results = ParentAccess.objects.filter(
                parent=parent,
                results_access=True
            ).exists()

    return render(
        request,
        "accounts/parent_dashboard.html",
        {
            "parent": parent,
            "children": children,
        }
    )

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from teachers.models import StudentScore
from students.models import Student
from parents.models import ParentAccess


@login_required
def parent_test_detail(request, student_id, test_type):

    profile = request.user.userprofile
    parent = profile.parent_profile

    # Make sure the parent can only view their own child
    child = get_object_or_404(
        Student,
        id=student_id,
        parent=parent
    )

    # Check results access
    # Parents with no outstanding balance are automatically allowed.
    # Parents with an outstanding balance need admin approval.
    if child.school_balance > 0:

        access = ParentAccess.objects.filter(
            parent=parent,
            results_access=True
        ).first()

        if not access:
            return redirect("parent_dashboard")

    scores = (
        StudentScore.objects
        .filter(
            student=child,
            test__test_type=test_type
        )
        .select_related("test", "test__subject")
    )

    total_score = 0
    total_max = 0

    for score in scores:

        # Calculate performance information
        if score.score is not None and score.test.max_score:

            total_score += score.score
            total_max += score.test.max_score

            percentage = (
                score.score / score.test.max_score
            ) * 100

            score.percentage = round(percentage, 2)

            # Performance category
            if percentage >= 80:
                score.performance = "Excellent"
                score.performance_color = "green"

            elif percentage >= 60:
                score.performance = "Can do Better"
                score.performance_color = "yellow"

            elif percentage >= 40:
                score.performance = "Needs Improvement"
                score.performance_color = "orange"

            else:
                score.performance = "Needs Attention"
                score.performance_color = "red"

        else:

            score.percentage = 0
            score.performance = "Not Graded"
            score.performance_color = "gray"

    # Overall average
    average = (
        round((total_score / total_max) * 100, 2)
        if total_max > 0
        else 0
    )

    return render(
        request,
        "accounts/parent_test_detail.html",
        {
            "child": child,
            "scores": scores,
            "test_type": test_type,
            "total_score": total_score,
            "total_max": total_max,
            "average": average,
        }
    )
# accounts/views.py
from django.shortcuts import redirect
from django.contrib.auth import logout

def user_logout(request):
    logout(request)
    return redirect('home')  # redirect to homepage after logout


















def is_school_admin(user):
    return user.is_authenticated and user.is_staff







from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404

from students.models import Student, Grade




from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from students.models import Student, Grade
from fees.models import Payment


def is_school_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_school_admin, login_url="/admin/login/")
def school_admin_dashboard(request):

    pending_payments_count = Payment.objects.filter(
        status="pending"
    ).count()

    return render(
        request,
        "accounts/school_admin_dashboard.html",
        {
            "pending_payments_count": pending_payments_count,
        }
    )


@user_passes_test(is_school_admin, login_url="/admin/login/")
def pending_payments(request):

    payments = (
        Payment.objects
        .filter(status="pending")
        .select_related(
            "student",
            "student__profile",
            "parent",
            "parent__profile",
            "parent__profile__user",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "accounts/pending_payments.html",
        {
            "payments": payments,
        }
    )


@user_passes_test(is_school_admin, login_url="/admin/login/")
def payment_verification_detail(request, payment_id):

    payment = get_object_or_404(
        Payment.objects.select_related(
            "student",
            "student__profile",
            "parent",
            "parent__profile",
            "parent__profile__user",
        ),
        id=payment_id
    )

    return render(
        request,
        "accounts/payment_verification_detail.html",
        {
            "payment": payment,
        }
    )


@user_passes_test(is_school_admin, login_url="/admin/login/")
def confirm_payment(request, payment_id):

    payment = get_object_or_404(
        Payment,
        id=payment_id
    )

    if request.method != "POST":
        return redirect(
            "payment_verification_detail",
            payment_id=payment.id
        )

    if payment.status != "pending":
        messages.warning(
            request,
            "This payment has already been processed."
        )

        return redirect(
            "payment_verification_detail",
            payment_id=payment.id
        )

    payment.status = "confirmed"
    payment.confirmed_by = request.user
    payment.confirmed_at = timezone.now()
    payment.rejection_reason = ""

    payment.save(
        update_fields=[
            "status",
            "confirmed_by",
            "confirmed_at",
            "rejection_reason",
        ]
    )

    messages.success(
        request,
        "Payment confirmed successfully. The learner's school balance was not changed."
    )

    return redirect("pending_payments")


@user_passes_test(is_school_admin, login_url="/admin/login/")
def reject_payment(request, payment_id):

    payment = get_object_or_404(
        Payment,
        id=payment_id
    )

    if request.method != "POST":
        return redirect(
            "payment_verification_detail",
            payment_id=payment.id
        )

    if payment.status != "pending":
        messages.warning(
            request,
            "This payment has already been processed."
        )

        return redirect(
            "payment_verification_detail",
            payment_id=payment.id
        )

    rejection_reason = request.POST.get(
        "rejection_reason",
        ""
    ).strip()

    if not rejection_reason:
        messages.error(
            request,
            "Please provide a reason for rejecting this payment."
        )

        return redirect(
            "payment_verification_detail",
            payment_id=payment.id
        )

    payment.status = "rejected"
    payment.rejection_reason = rejection_reason
    payment.confirmed_by = request.user
    payment.confirmed_at = timezone.now()

    payment.save(
        update_fields=[
            "status",
            "rejection_reason",
            "confirmed_by",
            "confirmed_at",
        ]
    )

    messages.success(
        request,
        "Payment rejected successfully."
    )

    return redirect("pending_payments")






def is_django_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_django_admin, login_url="/system-admin/login/")
def class_lists(request):
    grades = Grade.objects.all().order_by("name")

    return render(
        request,
        "accounts/class_lists.html",
        {
            "grades": grades,
        }
    )


@user_passes_test(is_django_admin, login_url="/system-admin/login/")
def class_list_detail(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)

    students = Student.objects.filter(
        grade=grade,
        is_active=True
    ).select_related(
        "parent",
        "profile",
        "profile__user"
    ).order_by("first_name", "last_name")

    return render(
        request,
        "accounts/class_list_detail.html",
        {
            "grade": grade,
            "students": students,
        }
    )



from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect

from students.models import Student, Grade
from parents.models import ParentAccess


def is_school_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_school_admin, login_url="/admin/login/")
def parent_access_control(request):
    grades = Grade.objects.all().order_by("name")

    return render(
        request,
        "accounts/parent_access_control.html",
        {
            "grades": grades,
        }
    )


@user_passes_test(is_school_admin, login_url="/admin/login/")
def parent_access_grade(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)

    students = Student.objects.filter(
        grade=grade,
        is_active=True
    ).select_related(
        "parent",
        "parent__profile",
        "parent__profile__user",
        "profile",
        "profile__user"
    ).order_by(
        "first_name",
        "last_name"
    )

    # Make sure every parent has an access-control record
    for student in students:
        if student.parent:
            ParentAccess.objects.get_or_create(
                parent=student.parent
            )

    return render(
        request,
        "accounts/parent_access_grade.html",
        {
            "grade": grade,
            "students": students,
        }
    )


@user_passes_test(is_school_admin, login_url="/admin/login/")
def update_parent_access(request, parent_id):
    parent_access = get_object_or_404(
        ParentAccess,
        parent_id=parent_id
    )

    if request.method == "POST":

        if parent_access.results_access:
            parent_access.results_access = False
            action = "revoked"
        else:
            parent_access.results_access = True
            action = "granted"

        parent_access.save()

        messages.success(
            request,
            f"Results access successfully {action}."
        )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "parent_access_control"
        )
    )