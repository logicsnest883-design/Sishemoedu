from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from students.models import Grade, Student
from parents.models import Parent






from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages




@login_required
def parent_grade_list(request):
    """
    Show all grades so the admin can select a grade to see its parents.
    """
    grades = Grade.objects.all()
    return render(
        request,
        "parents/parent_grade_list.html",
        {"grades": grades}
    )


@login_required
def parents_in_grade(request, grade_id):
    """
    Show all parents who have students in a specific grade.
    """
    grade = get_object_or_404(Grade, id=grade_id)

    # Get all Parent objects linked to students in this grade
    parents = Parent.objects.filter(
        children__grade=grade
    ).distinct()

    # Prefetch related students to avoid N+1 queries
    parents = parents.prefetch_related(
        "children__profile"
    )

    return render(
        request,
        "parents/parents_in_grade.html",
        {
            "grade": grade,
            "parents": parents,
        }
    )


@login_required
def parent_detail(request, parent_id):
    """
    Show details of a single parent, including their students.
    """
    parent = get_object_or_404(
        Parent,
        id=parent_id
    )

    # Get all students linked to this parent
    students = parent.children.select_related("grade", "profile").all()

    return render(
        request,
        "parents/parent_detail.html",
        {
            "parent": parent,
            "students": students,
        }
    )



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ParentCreateForm

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ParentCreateForm


@login_required
def create_parent(request):
    if request.method == "POST":
        form = ParentCreateForm(request.POST)
        if form.is_valid():
            parent = form.save()
            messages.success(request, f"Parent '{parent.full_name()}' created successfully!")
            return redirect("parents:parent_grade_list")
        else:
            # Form errors will now show in template
            messages.error(request, "Please fix the errors below.")
    else:
        form = ParentCreateForm()

    return render(
        request,
        "parents/create_parent.html",
        {"form": form}
    )


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Parent
from students.models import Student
from teachers.models import Attendance

@login_required
def parent_dashboard(request):
    # get parent from userprofile
    profile = request.user.userprofile
    parent = profile.parent_profile  # <-- THIS is your correct link

    # children linked to parent (adjust field if needed)
    children = Student.objects.filter(parent=parent)

    for child in children:
        records = Attendance.objects.filter(student=child)

        total = records.count()
        present = records.filter(status="P").count()

        child.attendance_percentage = round((present / total) * 100, 2) if total > 0 else 0

        latest = records.order_by("-week").first()
        child.latest_week = latest.week if latest else None

    return render(request, "parents/dashboard.html", {
        "parent": parent,
        "children": children
    })




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from students.models import Student
from teachers.models import Attendance, Test, StudentScore


@login_required
def parent_child_detail(request, student_id):
    profile = request.user.userprofile

    # ensure parent only accesses own child
    parent = profile.parent_profile

    child = get_object_or_404(
        Student,
        id=student_id,
        parent=parent
    )

    # Attendance
    records = Attendance.objects.filter(student=child)

    total = records.count()
    present = records.filter(status="P").count()

    attendance_percentage = round((present / total) * 100, 2) if total > 0 else 0

    # Latest tests summary
    scores = StudentScore.objects.filter(student=child).select_related("test", "test__subject")

    # group by test type
    tests_by_type = {}
    for score in scores:
        ttype = score.test.test_type
        if ttype not in tests_by_type:
            tests_by_type[ttype] = []
        tests_by_type[ttype].append(score)

    return render(request, "parents/child_detail.html", {
        "child": child,
        "attendance_percentage": attendance_percentage,
        "tests_by_type": tests_by_type
    })