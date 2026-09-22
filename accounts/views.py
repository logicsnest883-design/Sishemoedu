from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from teachers.views import (
    calculate_grade7_best6,
    calculate_secondary_best6,
    secondary_points,
)



from io import BytesIO

from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from django.http import FileResponse, HttpResponse






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
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            try:
                profile = user.userprofile

                if profile.role == "parent":
                    login(request, user)
                    return redirect("parent_dashboard")
                else:
                    messages.error(
                        request,
                        "You are not allowed to access the parent portal."
                    )

            except UserProfile.DoesNotExist:
                messages.error(
                    request,
                    "Profile not found. Contact system administrator."
                )
        else:
            messages.error(
                request,
                "Invalid username or password."
            )

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
    if child.school_balance > 920:

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
            "student__profile__user",
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


from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone


@user_passes_test(is_school_admin, login_url="/admin/login/")
def confirm_payment(request, payment_id):

    if request.method != "POST":
        return redirect(
            "payment_verification_detail",
            payment_id=payment_id
        )

    with transaction.atomic():

        payment = get_object_or_404(
            Payment.objects.select_for_update(),
            id=payment_id
        )

        # Prevent processing the same payment more than once
        if payment.status != "pending":

            messages.warning(
                request,
                "This payment has already been processed."
            )

            return redirect(
                "payment_verification_detail",
                payment_id=payment.id
            )

        # Only school fees reduces the learner's outstanding balance
        school_fees_amount = payment.fees_amount

        payment.student.school_balance -= school_fees_amount

        payment.student.save(
            update_fields=["school_balance"]
        )

        # Mark payment as confirmed
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
        f"Payment confirmed. K{school_fees_amount:.2f} "
        f"has been deducted from the learner's school balance."
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














from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404

from students.models import Student, Grade
from fees.models import Payment
from teachers.models import Test, StudentScore, Attendance
from Core.models import Subject


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
def admin_tests(request):

    grades = Grade.objects.all().order_by("name")

    return render(
        request,
        "accounts/admin_tests.html",
        {
            "grades": grades,
        }
    )


@user_passes_test(is_school_admin, login_url="/admin/login/")
def admin_grade_tests(request, grade_id):

    grade = get_object_or_404(Grade, id=grade_id)

    tests = (
        Test.objects
        .filter(grade=grade)
        .values(
            "test_type",
            "term",
            "year",
        )
        .distinct()
        .order_by("-year", "term", "test_type")
    )

    return render(
        request,
        "accounts/admin_grade_tests.html",
        {
            "grade": grade,
            "tests": tests,
        }
    )


@user_passes_test(is_school_admin, login_url="/admin/login/")
def admin_mark_schedule(request, grade_id, test_type):

    grade = get_object_or_404(Grade, id=grade_id)

    year = request.GET.get("year")
    term = request.GET.get("term")

    if not year or not term:
        return render(
            request,
            "accounts/admin_mark_schedule.html",
            {
                "grade": grade,
                "test_type": test_type,
                "error": "Year and term are required.",
            }
        )

    try:
        year = int(year)
    except (ValueError, TypeError):
        return render(
            request,
            "accounts/admin_mark_schedule.html",
            {
                "grade": grade,
                "test_type": test_type,
                "error": "Invalid academic year.",
            }
        )

    subjects = (
        Subject.objects
        .filter(section__grades__name=grade.name)
        .distinct()
        .order_by("name")
    )

    tests = (
        Test.objects
        .filter(
            grade=grade,
            test_type=test_type,
            term=term,
            year=year,
        )
        .select_related("subject")
    )

    students = (
        Student.objects
        .filter(grade=grade)
        .select_related("profile__user")
        .order_by("first_name", "last_name")
    )

    is_grade7 = (
        grade.name.strip().lower() == "grade 7"
    )

    rows = []

    for student in students:

        subject_scores = []

        for subject in subjects:

            test = tests.filter(
                subject=subject
            ).first()

            score = None
            percentage = None
            points = None

            if test:

                score_obj = (
                    StudentScore.objects
                    .filter(
                        student=student,
                        test=test,
                    )
                    .first()
                )

                if score_obj and score_obj.score is not None:

                    score = score_obj.score

                    percentage = round(
                        (score / test.max_score) * 100,
                        2
                    )

                    if not is_grade7:
                        points = secondary_points(
                            percentage
                        )

            subject_scores.append({
                "subject": subject,
                "score": score,
                "max_score": test.max_score if test else None,
                "percentage": percentage,
                "points": points,
            })

        if is_grade7:

            best6 = calculate_grade7_best6(
                subject_scores
            )

            total = best6["total"]
            average = best6["average"]
            best6_subjects = best6["subjects"]

            secondary_total_points = None

        else:

            entered_subjects = [
                item
                for item in subject_scores
                if item["score"] is not None
            ]

            total = sum(
                item["score"]
                for item in entered_subjects
            )

            average = (
                round(
                    sum(
                        item["percentage"]
                        for item in entered_subjects
                    ) / len(entered_subjects),
                    2
                )
                if entered_subjects
                else 0
            )

            secondary_best6 = calculate_secondary_best6(
                subject_scores
            )

            best6_subjects = secondary_best6["subjects"]

            secondary_total_points = (
                secondary_best6["total"]
                if secondary_best6["count"] > 0
                else None
            )

        rows.append({
            "student": student,
            "subject_scores": subject_scores,
            "total": total,
            "average": average,
            "best6_subjects": best6_subjects,
            "secondary_total_points": secondary_total_points,
        })

    if is_grade7:

        rows.sort(
            key=lambda x: x["total"],
            reverse=True
        )

    else:

        rows.sort(
            key=lambda x: (
                x["secondary_total_points"]
                if x["secondary_total_points"] is not None
                else 9999
            )
        )

    current_position = 0
    previous_value = None

    for index, row in enumerate(rows, start=1):

        if is_grade7:
            current_value = row["total"]
        else:
            current_value = row["secondary_total_points"]

        if current_value != previous_value:
            current_position = index

        row["position"] = (
            current_position
            if current_value is not None
            else None
        )

        previous_value = current_value

    return render(
        request,
        "accounts/admin_mark_schedule.html",
        {
            "grade": grade,
            "subjects": subjects,
            "rows": rows,
            "test_type": test_type,
            "year": year,
            "term": term,
            "is_grade7": is_grade7,
        }
    )











@user_passes_test(is_school_admin, login_url="/admin/login/")
def download_mark_schedule_pdf(request, grade_id, test_type):

    grade = get_object_or_404(Grade, id=grade_id)

    year = request.GET.get("year")
    term = request.GET.get("term")

    if not year or not term:
        return HttpResponse(
            "Year and term are required.",
            status=400
        )

    try:
        year = int(year)
    except (ValueError, TypeError):
        return HttpResponse(
            "Invalid academic year.",
            status=400
        )

    subjects = (
        Subject.objects
        .filter(section__grades__name=grade.name)
        .distinct()
        .order_by("name")
    )

    tests = (
        Test.objects
        .filter(
            grade=grade,
            test_type=test_type,
            term=term,
            year=year,
        )
        .select_related("subject")
    )

    students = (
        Student.objects
        .filter(grade=grade)
        .select_related("profile__user")
        .order_by("first_name", "last_name")
    )

    is_grade7 = (
        grade.name.strip().lower() == "grade 7"
    )

    rows = []

    for student in students:

        subject_scores = []

        for subject in subjects:

            test = tests.filter(
                subject=subject
            ).first()

            score = None
            percentage = None
            points = None

            if test:

                score_obj = (
                    StudentScore.objects
                    .filter(
                        student=student,
                        test=test,
                    )
                    .first()
                )

                if score_obj and score_obj.score is not None:

                    score = score_obj.score

                    percentage = round(
                        (score / test.max_score) * 100,
                        2
                    )

                    if not is_grade7:
                        points = secondary_points(
                            percentage
                        )

            subject_scores.append({
                "subject": subject,
                "score": score,
                "max_score": test.max_score if test else None,
                "percentage": percentage,
                "points": points,
            })

        if is_grade7:

            best6 = calculate_grade7_best6(
                subject_scores
            )

            total = best6["total"]
            average = best6["average"]
            best6_subjects = best6["subjects"]

            secondary_total_points = None

        else:

            entered_subjects = [
                item
                for item in subject_scores
                if item["score"] is not None
            ]

            total = sum(
                item["score"]
                for item in entered_subjects
            )

            average = (
                round(
                    sum(
                        item["percentage"]
                        for item in entered_subjects
                    ) / len(entered_subjects),
                    2
                )
                if entered_subjects
                else 0
            )

            secondary_best6 = calculate_secondary_best6(
                subject_scores
            )

            best6_subjects = secondary_best6["subjects"]

            secondary_total_points = (
                secondary_best6["total"]
                if secondary_best6["count"] > 0
                else None
            )

        rows.append({
            "student": student,
            "subject_scores": subject_scores,
            "total": total,
            "average": average,
            "best6_subjects": best6_subjects,
            "secondary_total_points": secondary_total_points,
        })

    if is_grade7:

        rows.sort(
            key=lambda x: x["total"],
            reverse=True
        )

    else:

        rows.sort(
            key=lambda x: (
                x["secondary_total_points"]
                if x["secondary_total_points"] is not None
                else 9999
            )
        )

    current_position = 0
    previous_value = None

    for index, row in enumerate(rows, start=1):

        if is_grade7:
            current_value = row["total"]
        else:
            current_value = row["secondary_total_points"]

        if current_value != previous_value:
            current_position = index

        row["position"] = (
            current_position
            if current_value is not None
            else None
        )

        previous_value = current_value

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=8 * mm,
        leftMargin=8 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ScheduleTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "ScheduleSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=8,
    )

    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.5,
        leading=7,
        alignment=TA_CENTER,
        textColor=colors.white,
    )

    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.2,
        leading=7,
        alignment=TA_CENTER,
    )

    student_style = ParagraphStyle(
        "StudentCell",
        parent=cell_style,
        alignment=TA_LEFT,
        fontName="Helvetica-Bold",
    )

    key_style = ParagraphStyle(
        "Key",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        alignment=TA_LEFT,
    )

    story = []

    story.append(
        Paragraph(
            "MARK SCHEDULE",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"<b>{grade.name}</b> &nbsp; • &nbsp; "
            f"{test_type} &nbsp; • &nbsp; "
            f"Year {year} &nbsp; • &nbsp; "
            f"{term}",
            subtitle_style
        )
    )

    if is_grade7:

        key_text = (
            "<b>Grading Key:</b> "
            "Special Paper 1 and Special Paper 2 are compulsory. "
            "Four highest-scoring remaining subjects complete the Best 6."
        )

    else:

        key_text = (
            "<b>Grading Key:</b> "
            "85–100 = 1 &nbsp;&nbsp; "
            "75–84 = 2 &nbsp;&nbsp; "
            "70–74 = 3 &nbsp;&nbsp; "
            "65–69 = 4 &nbsp;&nbsp; "
            "60–64 = 5 &nbsp;&nbsp; "
            "55–59 = 6 &nbsp;&nbsp; "
            "50–54 = 7 &nbsp;&nbsp; "
            "45–49 = 8 &nbsp;&nbsp; "
            "40–44 = 9 &nbsp;&nbsp; "
            "Below 40 = Fail"
        )

    story.append(
        Paragraph(
            key_text,
            key_style
        )
    )

    story.append(
        Spacer(1, 6)
    )

    headers = [
        Paragraph("Student", header_style)
    ]

    for subject in subjects:

        subject_name = subject.name

        if (
            is_grade7
            and subject_name.strip().lower()
            in ["special paper 1", "special paper 2"]
        ):
            subject_name += "<br/><font size='5'>COMPULSORY</font>"

        headers.append(
            Paragraph(
                subject_name,
                header_style
            )
        )

    if is_grade7:

        headers.extend([
            Paragraph("Best 6", header_style),
            Paragraph("Average", header_style),
            Paragraph("Pos.", header_style),
        ])

    else:

        headers.extend([
            Paragraph("Total", header_style),
            Paragraph("Best 6<br/>Points", header_style),
            Paragraph("Average", header_style),
            Paragraph("Pos.", header_style),
        ])

    table_data = [headers]

    for index, row in enumerate(rows, start=1):

        student = row["student"]

        if (
            student.first_name
            or student.last_name
        ):
            student_name = (
                f"{student.first_name} "
                f"{student.last_name}"
            ).strip()
        else:
            student_name = (
                student.profile.user.get_full_name()
            )

        data_row = [
            Paragraph(
                student_name,
                student_style
            )
        ]

        for item in row["subject_scores"]:

            if item["score"] is not None:

                score_text = str(item["score"])

                if (
                    not is_grade7
                    and item["points"] is not None
                ):
                    score_text += (
                        f"<br/><font size='5'>"
                        f"{item['points']} pts"
                        f"</font>"
                    )

            else:

                score_text = "—"

            data_row.append(
                Paragraph(
                    score_text,
                    cell_style
                )
            )

        if is_grade7:

            data_row.extend([
                Paragraph(
                    str(row["total"]),
                    cell_style
                ),
                Paragraph(
                    str(row["average"]),
                    cell_style
                ),
                Paragraph(
                    str(row["position"])
                    if row["position"] is not None
                    else "—",
                    cell_style
                ),
            ])

        else:

            data_row.extend([
                Paragraph(
                    str(row["total"]),
                    cell_style
                ),
                Paragraph(
                    str(row["secondary_total_points"])
                    if row["secondary_total_points"] is not None
                    else "—",
                    cell_style
                ),
                Paragraph(
                    f"{row['average']}%",
                    cell_style
                ),
                Paragraph(
                    str(row["position"])
                    if row["position"] is not None
                    else "—",
                    cell_style
                ),
            ])

        table_data.append(data_row)

    page_width = landscape(A4)[0] - 16 * mm
    student_width = 42 * mm

    remaining_columns = len(headers) - 1

    subject_width = (
        page_width - student_width
    ) / remaining_columns

    column_widths = [
        student_width
    ] + [
        subject_width
        for _ in range(remaining_columns)
    ]

    table = Table(
        table_data,
        colWidths=column_widths,
        repeatRows=1,
        hAlign="CENTER",
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0F766E"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.HexColor("#D1D5DB"),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "CENTER",
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, -1),
                colors.white,
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F8FAFC"),
                ],
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 8)
    )

    story.append(
        Paragraph(
            "Generated from the school management system.",
            ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                fontSize=6.5,
                textColor=colors.HexColor("#6B7280"),
                alignment=TA_CENTER,
            )
        )
    )

    document.build(story)

    buffer.seek(0)

    filename = (
        f"{grade.name}_"
        f"{test_type}_"
        f"{term}_"
        f"{year}_"
        f"Mark_Schedule.pdf"
    )

    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )






@user_passes_test(is_school_admin, login_url="/admin/login/")
def admin_attendance(request):
    grades = Grade.objects.all().order_by("name")

    return render(
        request,
        "accounts/admin_attendance.html",
        {
            "grades": grades,
        }
    )


@user_passes_test(is_school_admin, login_url="/admin/login/")
def admin_grade_attendance(request, grade_id):
    grade = get_object_or_404(
        Grade,
        id=grade_id
    )

    years = range(2026, 2031)

    terms = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    ]

    weeks = range(1, 14)

    if request.method == "POST":

        year = request.POST.get("year")
        term = request.POST.get("term")
        week = request.POST.get("week")

        if not year or not term or not week:
            messages.error(
                request,
                "Please select the year, term and week."
            )
            return redirect(
                "admin_grade_attendance",
                grade_id=grade.id
            )

        try:
            year = int(year)
            week = int(week)
        except (ValueError, TypeError):
            messages.error(
                request,
                "Invalid year or week."
            )
            return redirect(
                "admin_grade_attendance",
                grade_id=grade.id
            )

        return redirect(
            f"{reverse('admin_attendance_detail', kwargs={'grade_id': grade.id, 'year': year, 'term': term, 'week': week})}"
        )

    return render(
        request,
        "accounts/admin_grade_attendance.html",
        {
            "grade": grade,
            "years": years,
            "terms": terms,
            "weeks": weeks,
        }
    )


@user_passes_test(is_school_admin, login_url="/admin/login/")
def admin_attendance_detail(
    request,
    grade_id,
    year,
    term,
    week
):
    grade = get_object_or_404(
        Grade,
        id=grade_id
    )

    students = list(
        Student.objects
        .filter(grade=grade)
        .select_related("profile__user")
        .order_by("profile__user__first_name", "profile__user__last_name")
    )

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    ]

    rows = []

    total_present = 0
    total_days = 0

    for student in students:

        current_week_records = Attendance.objects.filter(
            student=student,
            year=year,
            term=term,
            week=week
        )

        attendance_map = {}

        for record in current_week_records:
            attendance_map[record.day] = record.status

        day_records = []

        for day in days:
            day_records.append({
                "day": day,
                "status": attendance_map.get(day, "")
            })

        all_records = Attendance.objects.filter(
            student=student,
            year=year,
            term=term,
            week__lte=week
        )

        present = all_records.filter(
            status="P"
        ).count()

        absent = all_records.filter(
            status="A"
        ).count()

        recorded = all_records.count()

        percentage = (
            round(
                (present / recorded) * 100,
                2
            )
            if recorded > 0
            else 0
        )

        total_present += present
        total_days += recorded

        rows.append({
            "student": student,
            "days": day_records,
            "present": present,
            "absent": absent,
            "percentage": percentage,
        })

    overall_percentage = (
        round(
            (total_present / total_days) * 100,
            2
        )
        if total_days > 0
        else 0
    )

    return render(
        request,
        "accounts/admin_attendance_detail.html",
        {
            "grade": grade,
            "year": year,
            "term": term,
            "week": week,
            "days": days,
            "rows": rows,
            "overall_percentage": overall_percentage,
        }
    )