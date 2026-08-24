from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import modelformset_factory
from .models import Test, StudentScore, Subject, TestType
from students.models import Grade, Student
from .forms import StudentScoreForm
from django.utils import timezone


@login_required
def teacher_dashboard(request):

    profile = request.user.userprofile

    # ---------------------------------
    # CHECK TEACHER ACCESS
    # ---------------------------------
    if profile.role != "teacher":
        messages.error(request, "Access denied.")
        return redirect("teacher_login")

    # ---------------------------------
    # GET ASSIGNED GRADE
    # ---------------------------------
    try:
        grade = profile.assigned_grade
    except Grade.DoesNotExist:
        messages.error(request, "No grade assigned to you.")
        return redirect("teacher_login")

    # ---------------------------------
    # CURRENT ACADEMIC PERIOD
    # ---------------------------------
    current_year = 2026
    current_term = "Term 1"

    # ---------------------------------
    # AUTOMATICALLY ENSURE TESTS EXIST
    # FOR EVERY SUBJECT
    # ---------------------------------
    subjects = grade.subjects.all()

    for subject in subjects:

        for test_type_value, _ in TestType.choices:

            Test.objects.get_or_create(
                grade=grade,
                subject=subject,
                test_type=test_type_value,
                term=current_term,
                year=current_year,
                defaults={
                    "max_score": 100
                }
            )

    # ---------------------------------
    # FETCH TESTS FOR CURRENT PERIOD
    # ---------------------------------
    tests_by_type = {}

    for test_type_value, test_type_label in TestType.choices:

        tests_by_type[test_type_label] = Test.objects.filter(
            grade=grade,
            test_type=test_type_value,
            term=current_term,
            year=current_year
        ).select_related("subject")

    # ---------------------------------
    # FETCH STUDENTS
    # ---------------------------------
    students = Student.objects.filter(
        grade=grade
    )

    # ---------------------------------
    # CONTEXT
    # ---------------------------------
    context = {
        "grade": grade,
        "students": students,
        "tests_by_type": tests_by_type,

        # Academic period
        "current_year": current_year,
        "current_term": current_term,
    }

    return render(
        request,
        "accounts/teacher_dashboard.html",
        context
    )


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Test, StudentScore, Subject
from students.models import Student

@login_required
def enter_scores_grid(request, test_type):

    profile = request.user.userprofile

    # =========================
    # TEACHER ACCESS
    # =========================
    if profile.role != "teacher":
        messages.error(request, "Access denied.")
        return redirect("teacher_login")

    grade = profile.assigned_grade

    if not grade:
        messages.error(request, "No grade assigned to you.")
        return redirect("teacher_dashboard")

    # =========================
    # GET YEAR AND TERM
    # =========================
    year = request.GET.get("year")
    term = request.GET.get("term")

    if not year or not term:
        messages.error(
            request,
            "Please select the academic year and term first."
        )
        return redirect("enter_scores_list")

    try:
        year = int(year)
    except (ValueError, TypeError):
        messages.error(request, "Invalid academic year.")
        return redirect("enter_scores_list")

    # =========================
    # STUDENTS
    # =========================
    students = Student.objects.filter(
        grade=grade
    ).select_related("profile__user")

    # =========================
    # SUBJECTS
    # =========================
    subjects = Subject.objects.filter(
        grade=grade
    ).order_by("name")

    # =========================
    # ENSURE TESTS EXIST
    # FOR THIS YEAR + TERM
    # =========================
    for subject in subjects:

        Test.objects.get_or_create(
            grade=grade,
            subject=subject,
            test_type=test_type,
            term=term,
            year=year,
            defaults={
                "max_score": 100
            }
        )

    # =========================
    # GET TESTS
    # =========================
    tests = Test.objects.filter(
        grade=grade,
        test_type=test_type,
        term=term,
        year=year
    ).select_related("subject")

    # =========================
    # HANDLE FORM SUBMISSION
    # =========================
    if request.method == "POST":

        errors = []

        for student in students:

            for subject in subjects:

                field_name = f"score_{student.id}_{subject.id}"

                value = request.POST.get(field_name)

                test = tests.filter(
                    subject=subject
                ).first()

                # No test should normally occur because
                # we created them above.
                if not test:
                    continue

                # Empty input means leave it unchanged
                if value in (None, ""):
                    continue

                try:
                    score_value = int(value)

                except (ValueError, TypeError):

                    errors.append(
                        f"Invalid score for "
                        f"{student.first_name} "
                        f"{student.last_name} - "
                        f"{subject.name}."
                    )

                    continue

                # Validate score
                if score_value < 0 or score_value > test.max_score:

                    errors.append(
                        f"{student.first_name} "
                        f"{student.last_name} - "
                        f"{subject.name}: "
                        f"score must be between 0 and "
                        f"{test.max_score}."
                    )

                    continue

                # =========================
                # SAVE SCORE
                # =========================
                score_obj, created = StudentScore.objects.get_or_create(
                    student=student,
                    test=test
                )

                score_obj.score = score_value
                score_obj.save()

        # =========================
        # DISPLAY ERRORS
        # =========================
        if errors:

            for error in errors:
                messages.error(request, error)

        else:

            messages.success(
                request,
                f"Scores saved successfully for "
                f"{test_type} - {term}, {year}."
            )

        return redirect(
            f"/enter-scores/{test_type}/?year={year}&term={term}"
        )

    # =========================
    # PREPARE DISPLAY DATA
    # =========================
    rows = []

    for student in students:

        subject_scores = []

        total = 0
        count = 0

        for subject in subjects:

            test = tests.filter(
                subject=subject
            ).first()

            if test:

                score_obj = StudentScore.objects.filter(
                    student=student,
                    test=test
                ).first()

                score_value = (
                    score_obj.score
                    if score_obj
                    else None
                )

                subject_scores.append({
                    "subject": subject,
                    "score": score_value,
                    "max_score": test.max_score,
                    "test_id": test.id,
                })

                # Only calculate using entered marks
                if score_value is not None:

                    total += score_value
                    count += 1

            else:

                subject_scores.append({
                    "subject": subject,
                    "score": None,
                    "max_score": None,
                    "test_id": None,
                })

        average = (
            round(total / count, 2)
            if count > 0
            else 0
        )

        rows.append({
            "student": student,
            "subject_scores": subject_scores,
            "total": total,
            "average": average,
        })

    # Highest total first
    rows = sorted(
        rows,
        key=lambda x: x["total"],
        reverse=True
    )

    # =========================
    # RENDER
    # =========================
    return render(
        request,
        "teachers/enter_scores_grid.html",
        {
            "rows": rows,
            "subjects": subjects,
            "test_type": test_type,
            "grade": grade,
            "year": year,
            "term": term,
        }
    )

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Test

@login_required
def view_tests(request):
    profile = request.user.userprofile

    if profile.role != "teacher":
        messages.error(request, "Access denied.")
        return redirect("teacher_login")

    grade = profile.assigned_grade

    tests = Test.objects.filter(grade=grade).select_related("subject").order_by("test_type", "subject__name")

    return render(request, "teachers/view_tests.html", {
        "grade": grade,
        "tests": tests
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import TestType
@login_required
def enter_scores_list(request):
    profile = request.user.userprofile

    if profile.role != "teacher":
        messages.error(request, "Access denied.")
        return redirect("teacher_login")

    grade = profile.assigned_grade

    if not grade:
        messages.error(request, "No grade assigned to you.")
        return redirect("teacher_dashboard")

    # -----------------------------
    # AVAILABLE YEARS
    # -----------------------------
    current_year = timezone.now().year

    years = range(current_year, current_year - 5, -1)

    terms = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    ]

    # -----------------------------
    # YEAR + TERM SELECTION
    # -----------------------------
    if request.method == "POST":

        year = request.POST.get("year")
        term = request.POST.get("term")

        if not year or not term:
            messages.error(
                request,
                "Please select both the academic year and term."
            )

            return redirect("enter_scores_list")

        return render(
            request,
            "teachers/enter_scores_list.html",
            {
                "grade": grade,
                "test_types": TestType.choices,
                "years": years,
                "terms": terms,
                "selected_year": int(year),
                "selected_term": term,
            }
        )

    # -----------------------------
    # FIRST VISIT
    # -----------------------------
    return render(
        request,
        "teachers/enter_scores_list.html",
        {
            "grade": grade,
            "years": years,
            "terms": terms,
            "test_types": TestType.choices,
        }
    )


from datetime import date
from .models import Attendance
from students.models import Student
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Attendance
from students.models import Student

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Attendance
from students.models import Student


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Attendance
from students.models import Student

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Attendance
from students.models import Student


@login_required
def class_register(request):
    profile = request.user.userprofile

    if profile.role != "teacher":
        messages.error(request, "Access denied.")
        return redirect("teacher_login")

    grade = profile.assigned_grade
    students = Student.objects.filter(grade=grade)

    weeks = range(1, 14)

    selected_week = int(request.POST.get("week", 1)) if request.method == "POST" else 1

    days = [
        ("1", "Monday"),
        ("2", "Tuesday"),
        ("3", "Wednesday"),
        ("4", "Thursday"),
        ("5", "Friday"),
    ]

    # ======================
    # SAVE ATTENDANCE
    # ======================
    if request.method == "POST":
        for student in students:
            for day_num, day_name in days:
                field_name = f"attendance_{student.id}_{day_num}"
                value = request.POST.get(field_name)

                if value in ["P", "A"]:
                    Attendance.objects.update_or_create(
                        student=student,
                        week=selected_week,
                        day=day_name,
                        defaults={"status": value}
                    )

        messages.success(request, "Attendance saved successfully.")
        return redirect(f"{request.path}?week={selected_week}")

    # ======================
    # LOAD DATA + RUNNING %
    # ======================
    for student in students:
        # default values for current week display
        student.mon = ""
        student.tue = ""
        student.wed = ""
        student.thu = ""
        student.fri = ""

        # 🔹 CURRENT WEEK RECORDS (for table display)
        current_week_records = Attendance.objects.filter(
            student=student,
            week=selected_week
        )

        for record in current_week_records:
            if record.day == "Monday":
                student.mon = record.status
            elif record.day == "Tuesday":
                student.tue = record.status
            elif record.day == "Wednesday":
                student.wed = record.status
            elif record.day == "Thursday":
                student.thu = record.status
            elif record.day == "Friday":
                student.fri = record.status

        # 🔹 ALL TERM RECORDS (Week 1 → current week)
        all_records = Attendance.objects.filter(
            student=student,
            week__lte=selected_week
        )

        total_days = all_records.count()
        present_days = all_records.filter(status="P").count()

        student.attendance_percentage = round(
            (present_days / total_days) * 100, 2
        ) if total_days > 0 else 0

    return render(request, "teachers/class_register.html", {
        "students": students,
        "weeks": weeks,
        "selected_week": selected_week,
    })