from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import modelformset_factory
from .models import Test, StudentScore, TestType
from students.models import Grade, Student
from .forms import StudentScoreForm
from django.utils import timezone
from Core.models import Subject


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
    subjects = Subject.objects.filter(
        section__grades__name=grade.name
    ).order_by("name")

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






def secondary_points(percentage):
    """
    Convert a percentage into the secondary-school points system.
    """

    if percentage >= 85:
        return 1
    elif percentage >= 75:
        return 2
    elif percentage >= 70:
        return 3
    elif percentage >= 65:
        return 4
    elif percentage >= 60:
        return 5
    elif percentage >= 55:
        return 6
    elif percentage >= 50:
        return 7
    elif percentage >= 45:
        return 8
    elif percentage >= 40:
        return 9

    return None




def calculate_secondary_best6(subject_scores):

    entered_subjects = [
        item
        for item in subject_scores
        if item.get("score") is not None
        and item.get("points") is not None
    ]

    entered_subjects.sort(
        key=lambda item: item["points"]
    )

    selected = entered_subjects[:6]

    total_points = sum(
        item["points"]
        for item in selected
    )

    return {
        "subjects": selected,
        "total": total_points,
        "count": len(selected),
    }


















def calculate_grade7_best6(subject_scores):
    """
    Grade 7 Best 6:

    1. Special Paper 1 is compulsory.
    2. Special Paper 2 is compulsory.
    3. Four highest remaining subjects are selected.
    4. Best 6 is calculated using the actual marks entered.
    5. Percentages are calculated only for display purposes.
    """

    compulsory = []
    other_subjects = []

    for item in subject_scores:

        score = item.get("score")
        max_score = item.get("max_score")
        subject = item.get("subject")

        if score is None or not max_score:
            continue

        percentage = round(
            (score / max_score) * 100,
            2
        )

        item["percentage"] = percentage

        subject_name = subject.name.strip().lower()

        if subject_name in [
            "special paper 1",
            "special paper 2",
        ]:
            compulsory.append(item)

        else:
            other_subjects.append(item)

    # Sort remaining subjects by actual marks
    other_subjects.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Select four highest remaining subjects
    selected_other = other_subjects[:4]

    # Special Paper 1 + Special Paper 2 + four highest subjects
    selected = compulsory + selected_other

    # Sort selected subjects by actual marks
    selected.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Best 6 total uses the actual marks entered
    total = sum(
        item["score"]
        for item in selected
    )

    # Average is also based on the actual marks
    best6_average = (
        round(total / len(selected), 2)
        if selected
        else 0
    )

    return {
        "subjects": selected,
        "total": total,
        "average": best6_average,
        "count": len(selected),
    }












@login_required
def enter_scores_grid(request, test_type):
    profile = request.user.userprofile

    if profile.role != "teacher":
        messages.error(request, "Access denied.")
        return redirect("teacher_login")

    grade = profile.assigned_grade

    if not grade:
        messages.error(request, "No grade assigned to you.")
        return redirect("teacher_dashboard")

    year = request.GET.get("year")
    term = request.GET.get("term")

    if not year or not term:
        messages.error(
            request,
            "Please select the academic year and term first.",
        )
        return redirect("enter_scores_list")

    try:
        year = int(year)
    except (ValueError, TypeError):
        messages.error(request, "Invalid academic year.")
        return redirect("enter_scores_list")

    students = Student.objects.filter(
        grade=grade
    ).select_related("profile__user")

    subjects = Subject.objects.filter(
        section__grades__name=grade.name
    ).order_by("name")

    correct_max_score = (
        150
        if grade.name.strip().lower() == "grade 7"
        else 100
    )

    for subject in subjects:
        test, created = Test.objects.get_or_create(
            grade=grade,
            subject=subject,
            test_type=test_type,
            term=term,
            year=year,
            defaults={
                "max_score": correct_max_score,
            },
        )

        if test.max_score != correct_max_score:
            test.max_score = correct_max_score
            test.save(
                update_fields=["max_score"]
            )

    tests = Test.objects.filter(
        grade=grade,
        test_type=test_type,
        term=term,
        year=year,
    ).select_related("subject")

    if request.method == "POST":
        errors = []

        for student in students:
            for subject in subjects:
                field_name = (
                    f"score_{student.id}_{subject.id}"
                )

                value = request.POST.get(field_name)

                test = tests.filter(
                    subject=subject
                ).first()

                if not test:
                    continue

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

                if (
                    score_value < 0
                    or score_value > test.max_score
                ):
                    errors.append(
                        f"{student.first_name} "
                        f"{student.last_name} - "
                        f"{subject.name}: "
                        f"score must be between 0 and "
                        f"{test.max_score}."
                    )
                    continue

                score_obj, created = (
                    StudentScore.objects.get_or_create(
                        student=student,
                        test=test,
                    )
                )

                score_obj.score = score_value
                score_obj.save()

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            messages.success(
                request,
                f"Scores saved successfully for "
                f"{test_type} - {term}, {year}.",
            )

        return redirect(
            f"/enter-scores/{test_type}/?year={year}&term={term}"
        )

    rows = []

    is_grade7 = (
        grade.name.strip().lower() == "grade 7"
    )

    is_secondary = (
        grade.name.strip().lower().startswith("form")
    )

    for student in students:
        subject_scores = []

        for subject in subjects:
            test = tests.filter(
                subject=subject
            ).first()

            if test:
                score_obj = StudentScore.objects.filter(
                    student=student,
                    test=test,
                ).first()

                score_value = (
                    score_obj.score
                    if score_obj
                    else None
                )

                percentage = None
                points = None

                if score_value is not None:
                    percentage = round(
                        (score_value / test.max_score) * 100,
                        2,
                    )

                    if is_secondary:
                        points = secondary_points(
                            percentage
                        )

                subject_scores.append(
                    {
                        "subject": subject,
                        "score": score_value,
                        "max_score": test.max_score,
                        "percentage": percentage,
                        "points": points,
                        "test_id": test.id,
                    }
                )

            else:
                subject_scores.append(
                    {
                        "subject": subject,
                        "score": None,
                        "max_score": None,
                        "percentage": None,
                        "points": None,
                        "test_id": None,
                    }
                )

        if is_grade7:
            best6 = calculate_grade7_best6(
                subject_scores
            )

            total = best6["total"]
            average = best6["average"]
            best6_subjects = best6["subjects"]

            secondary_total_points = None

        elif is_secondary:
            entered = [
                item
                for item in subject_scores
                if item["score"] is not None
            ]

            total = sum(
                item["score"]
                for item in entered
            )

            average = (
                round(
                    sum(
                        item["percentage"]
                        for item in entered
                    ) / len(entered),
                    2,
                )
                if entered
                else 0
            )

            secondary_best6 = calculate_secondary_best6(
                subject_scores
            )

            secondary_total_points = (
                secondary_best6["total"]
                if secondary_best6["count"] > 0
                else None
            )

            best6_subjects = secondary_best6["subjects"]

        else:
            entered = [
                item
                for item in subject_scores
                if item["score"] is not None
            ]

            total = sum(
                item["score"]
                for item in entered
            )

            average = (
                round(
                    sum(
                        item["percentage"]
                        for item in entered
                    ) / len(entered),
                    2,
                )
                if entered
                else 0
            )

            best6_subjects = []
            secondary_total_points = None

        rows.append(
            {
                "student": student,
                "subject_scores": subject_scores,
                "total": total,
                "average": average,
                "best6_subjects": best6_subjects,
                "secondary_total_points": secondary_total_points,
            }
        )

    rows = sorted(
        rows,
        key=lambda x: x["total"],
        reverse=True,
    )

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
            "is_grade7": is_grade7,
            "is_secondary": is_secondary,
        },
    )







from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Test

@login_required
def generate_mark_schedule(request, test_type):
    profile = request.user.userprofile

    if profile.role != "teacher":
        messages.error(request, "Access denied.")
        return redirect("teacher_login")

    grade = profile.assigned_grade

    if not grade:
        messages.error(request, "No grade assigned to you.")
        return redirect("teacher_dashboard")

    year = request.GET.get("year")
    term = request.GET.get("term")

    if not year or not term:
        messages.error(request, "Year and term are required.")
        return redirect("enter_scores_list")

    try:
        year = int(year)
    except (ValueError, TypeError):
        messages.error(request, "Invalid academic year.")
        return redirect("enter_scores_list")

    is_grade7 = (
        grade.name.strip().lower() == "grade 7"
    )

    is_secondary = (
        grade.name.strip().lower().startswith("form")
    )

    subjects = Subject.objects.filter(
        section__grades__name=grade.name
    ).order_by("name")

    tests = Test.objects.filter(
        grade=grade,
        test_type=test_type,
        term=term,
        year=year,
    ).select_related("subject")

    students = Student.objects.filter(
        grade=grade
    ).select_related("profile__user")

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
                score_obj = StudentScore.objects.filter(
                    student=student,
                    test=test,
                ).first()

                if (
                    score_obj
                    and score_obj.score is not None
                ):
                    score = score_obj.score

                    percentage = round(
                        (score / test.max_score) * 100,
                        2,
                    )

                    if is_secondary:
                        points = secondary_points(
                            percentage
                        )

            subject_scores.append(
                {
                    "subject": subject,
                    "score": score,
                    "max_score": (
                        test.max_score
                        if test
                        else None
                    ),
                    "percentage": percentage,
                    "points": points,
                }
            )

        if is_grade7:
            best6 = calculate_grade7_best6(
                subject_scores
            )

            best6_subjects = best6["subjects"]
            total = best6["total"]
            average = best6["average"]

            secondary_total_points = None

        elif is_secondary:
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
                    2,
                )
                if entered_subjects
                else 0
            )

            secondary_best6 = (
                calculate_secondary_best6(
                    subject_scores
                )
            )

            best6_subjects = (
                secondary_best6["subjects"]
            )

            secondary_total_points = (
                secondary_best6["total"]
                if secondary_best6["count"] > 0
                else None
            )

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
                    2,
                )
                if entered_subjects
                else 0
            )

            best6_subjects = []
            secondary_total_points = None

        rows.append(
            {
                "student": student,
                "subject_scores": subject_scores,
                "total": total,
                "average": average,
                "best6_subjects": best6_subjects,
                "secondary_total_points": (
                    secondary_total_points
                ),
            }
        )

    if is_grade7:
        rows = sorted(
            rows,
            key=lambda x: x["total"],
            reverse=True,
        )

    elif is_secondary:
        rows = sorted(
            rows,
            key=lambda x: (
                x["secondary_total_points"]
                if x["secondary_total_points"]
                is not None
                else 9999
            ),
        )

    else:
        rows = sorted(
            rows,
            key=lambda x: x["total"],
            reverse=True,
        )

    current_position = 0
    previous_value = None

    for index, row in enumerate(
        rows,
        start=1,
    ):
        if is_grade7:
            current_value = row["total"]

        elif is_secondary:
            current_value = (
                row["secondary_total_points"]
            )

        else:
            current_value = row["total"]

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
        "teachers/mark_schedule.html",
        {
            "grade": grade,
            "subjects": subjects,
            "rows": rows,
            "test_type": test_type,
            "year": year,
            "term": term,
            "is_grade7": is_grade7,
            "is_secondary": is_secondary,
        },
    )








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
from django.urls import reverse





@login_required
def teacher_attendance(request):
    profile = request.user.userprofile

    if profile.role != "teacher":
        messages.error(request, "Access denied.")
        return redirect("teacher_login")

    grade = profile.assigned_grade

    if not grade:
        messages.error(request, "No grade assigned to you.")
        return redirect("teacher_dashboard")

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
            return redirect("teacher_attendance")

        try:
            year = int(year)
            week = int(week)
        except (ValueError, TypeError):
            messages.error(
                request,
                "Invalid year or week."
            )
            return redirect("teacher_attendance")

        return redirect(
            f"{reverse('class_register')}?year={year}&term={term}&week={week}"
        )

    return render(
        request,
        "teachers/attendance_select.html",
        {
            "grade": grade,
            "years": years,
            "terms": terms,
            "weeks": weeks,
        }
    )


@login_required
def class_register(request):
    profile = request.user.userprofile

    if profile.role != "teacher":
        messages.error(request, "Access denied.")
        return redirect("teacher_login")

    grade = profile.assigned_grade

    if not grade:
        messages.error(
            request,
            "No grade assigned to you."
        )
        return redirect("teacher_dashboard")

    students = Student.objects.filter(
        grade=grade
    )

    days = [
        ("1", "Monday"),
        ("2", "Tuesday"),
        ("3", "Wednesday"),
        ("4", "Thursday"),
        ("5", "Friday"),
    ]

    weeks = range(1, 14)

    if request.method == "POST":

        year = request.POST.get("year")
        term = request.POST.get("term")
        selected_week = request.POST.get("week")

        if not year or not term or not selected_week:
            messages.error(
                request,
                "Year, term and week are required."
            )
            return redirect("teacher_attendance")

        try:
            year = int(year)
            selected_week = int(selected_week)
        except (ValueError, TypeError):
            messages.error(
                request,
                "Invalid year or week."
            )
            return redirect("teacher_attendance")

        for student in students:

            for day_num, day_name in days:

                field_name = f"attendance_{student.id}_{day_num}"
                value = request.POST.get(field_name)

                if value in ["P", "A"]:

                    Attendance.objects.update_or_create(
                        student=student,
                        year=year,
                        term=term,
                        week=selected_week,
                        day=day_name,
                        defaults={
                            "status": value
                        }
                    )

        messages.success(
            request,
            "Attendance saved successfully."
        )

        return redirect(
            f"{reverse('class_register')}?year={year}&term={term}&week={selected_week}"
        )

    year = request.GET.get("year")
    term = request.GET.get("term")
    selected_week = request.GET.get("week")

    if not year or not term or not selected_week:
        messages.error(
            request,
            "Please select the year, term and week first."
        )
        return redirect("teacher_attendance")

    try:
        year = int(year)
        selected_week = int(selected_week)
    except (ValueError, TypeError):
        messages.error(
            request,
            "Invalid attendance period."
        )
        return redirect("teacher_attendance")

    for student in students:

        student.mon = ""
        student.tue = ""
        student.wed = ""
        student.thu = ""
        student.fri = ""

        current_week_records = Attendance.objects.filter(
            student=student,
            year=year,
            term=term,
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

        all_records = Attendance.objects.filter(
            student=student,
            year=year,
            term=term,
            week__lte=selected_week
        )

        total_days = all_records.count()

        present_days = all_records.filter(
            status="P"
        ).count()

        student.attendance_percentage = (
            round(
                (present_days / total_days) * 100,
                2
            )
            if total_days > 0
            else 0
        )

    return render(
        request,
        "teachers/class_register.html",
        {
            "students": students,
            "weeks": weeks,
            "selected_week": selected_week,
            "year": year,
            "term": term,
            "days": days,
        }
    )