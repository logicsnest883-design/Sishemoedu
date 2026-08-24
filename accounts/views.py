from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile

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

    children = Student.objects.filter(parent=parent)

    for child in children:

        # -------------------------
        # ATTENDANCE
        # -------------------------
        records = Attendance.objects.filter(student=child)

        total = records.count()
        present = records.filter(status="P").count()

        child.attendance_percentage = round((present / total) * 100, 2) if total > 0 else 0

        # -------------------------
        # TESTS (NEW PART)
        # -------------------------
        scores = StudentScore.objects.filter(student=child).select_related("test")

        # group tests by type
        child.tests_by_type = {}

        for score in scores:
            test_type = score.test.test_type

            if test_type not in child.tests_by_type:
                child.tests_by_type[test_type] = []

            child.tests_by_type[test_type].append(score)

    return render(request, "accounts/parent_dashboard.html", {
        "parent": parent,
        "children": children
    })



from teachers.models import StudentScore
from students.models import Student

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

