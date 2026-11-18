
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from datetime import time
from django.db import transaction
from django.core.exceptions import ValidationError
from .forms import TimetableEntryFormSet

from .models import (
    Grade,
    Teacher,
    Subject,
    OptionGroup,
    Timetable,
    TimetableEntry,
)

from .forms import (
    GradeForm,
    TeacherForm,
    SubjectForm,
    OptionGroupForm,
    TimetableForm,
    TimetableEntryForm,
)


@login_required
def timetable_dashboard(request):
    context = {
        "grades": Grade.objects.filter(is_active=True),
        "teachers_count": Teacher.objects.filter(is_active=True).count(),
        "subjects_count": Subject.objects.filter(is_active=True).count(),
        "timetables_count": Timetable.objects.count(),
        "recent_timetables": Timetable.objects.select_related(
            "grade"
        ).order_by("-year", "term")[:10],
    }
    return render(request, "timetables/dashboard.html", context)


@login_required
def grade_list(request):
    grades = Grade.objects.all()
    return render(request, "timetables/grade_list.html", {
        "grades": grades
    })


@login_required
def grade_create(request):
    form = GradeForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Grade added successfully.")
        return redirect("timetables:grade_list")

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Add Grade",
        "cancel_url": reverse("timetables:grade_list"),
    })


@login_required
def grade_edit(request, pk):
    grade = get_object_or_404(Grade, pk=pk)
    form = GradeForm(request.POST or None, instance=grade)

    if form.is_valid():
        form.save()
        messages.success(request, "Grade updated successfully.")
        return redirect("timetables:grade_list")

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Edit Grade",
        "cancel_url": reverse("timetables:grade_list"),
    })


@login_required
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, "timetables/teacher_list.html", {
        "teachers": teachers
    })


@login_required
def teacher_create(request):
    form = TeacherForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Teacher added successfully.")
        return redirect("timetables:teacher_list")

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Add Teacher",
        "cancel_url": reverse("timetables:teacher_list"),
    })


@login_required
def teacher_edit(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    form = TeacherForm(request.POST or None, instance=teacher)

    if form.is_valid():
        form.save()
        messages.success(request, "Teacher updated successfully.")
        return redirect("timetables:teacher_list")

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Edit Teacher",
        "cancel_url": reverse("timetables:teacher_list"),
    })


@login_required
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, "timetables/subject_list.html", {
        "subjects": subjects
    })


@login_required
def subject_create(request):
    form = SubjectForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Subject added successfully.")
        return redirect("timetables:subject_list")

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Add Subject",
        "cancel_url": reverse("timetables:subject_list"),
    })


@login_required
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=subject)

    if form.is_valid():
        form.save()
        messages.success(request, "Subject updated successfully.")
        return redirect("timetables:subject_list")

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Edit Subject",
        "cancel_url": reverse("timetables:subject_list"),
    })


@login_required
def option_group_list(request):
    option_groups = OptionGroup.objects.select_related("grade").all()

    return render(request, "timetables/option_group_list.html", {
        "option_groups": option_groups,
    })


@login_required
def option_group_create(request):
    form = OptionGroupForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Option group added successfully.")
        return redirect("timetables:option_group_list")

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Add Option Group",
        "cancel_url": reverse("timetables:option_group_list"),
    })


@login_required
def option_group_edit(request, pk):
    option_group = get_object_or_404(OptionGroup, pk=pk)
    form = OptionGroupForm(request.POST or None, instance=option_group)

    if form.is_valid():
        form.save()
        messages.success(request, "Option group updated successfully.")
        return redirect("timetables:option_group_list")

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Edit Option Group",
        "cancel_url": reverse("timetables:option_group_list"),
    })


@login_required
@require_POST
def option_group_delete(request, pk):
    option_group = get_object_or_404(OptionGroup, pk=pk)
    option_group.delete()
    messages.success(request, "Option group deleted successfully.")
    return redirect("timetables:option_group_list")


@login_required
def timetable_list(request):
    timetables = Timetable.objects.select_related("grade").all()

    year = request.GET.get("year")
    term = request.GET.get("term")
    grade_id = request.GET.get("grade")

    if year:
        timetables = timetables.filter(year=year)

    if term:
        timetables = timetables.filter(term=term)

    if grade_id:
        timetables = timetables.filter(grade_id=grade_id)

    return render(request, "timetables/timetable_list.html", {
        "timetables": timetables,
        "grades": Grade.objects.filter(is_active=True),
        "selected_year": year or "",
        "selected_term": term or "",
        "selected_grade": grade_id or "",
        "term_choices": Timetable.TERM_CHOICES,
    })


@login_required
def timetable_create(request):
    form = TimetableForm(request.POST or None)

    if form.is_valid():
        timetable = form.save()
        messages.success(request, "Timetable created successfully.")
        return redirect("timetables:timetable_detail", pk=timetable.pk)

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Create Timetable",
        "cancel_url": reverse("timetables:timetable_list"),
    })


@login_required
def timetable_detail(request, pk):
    timetable = get_object_or_404(
        Timetable.objects.select_related("grade"), pk=pk
    )

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    duration = timetable.grade.lesson_duration

    slots = []

    def add_slot(start, end, kind="lesson", label=""):
        slots.append({
            "start": start,
            "end": end,
            "kind": kind,
            "label": label,
        })

    def add_lessons(start_hour, start_minute, end_hour, end_minute):
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute

        while start_minutes + duration <= end_minutes:
            next_minutes = start_minutes + duration

            add_slot(
                time(start_minutes // 60, start_minutes % 60),
                time(next_minutes // 60, next_minutes % 60),
            )

            start_minutes = next_minutes

    # Morning assembly or devotion
    add_slot(time(7, 30), time(8, 0), "morning")

    # Morning lessons
    if duration == 30:
        add_lessons(8, 0, 10, 0)
        add_slot(time(10, 0), time(10, 30), "break")
        add_lessons(10, 30, 13, 0)
    else:
        add_lessons(8, 0, 10, 40)
        add_slot(time(10, 40), time(11, 0), "break")
        add_lessons(11, 0, 13, 0)

    # Lunch
    add_slot(time(13, 0), time(14, 0), "lunch")

    # Afternoon lessons
    if duration == 30:
        add_lessons(14, 0, 15, 30)
    else:
        add_lessons(14, 0, 15, 20)
        add_slot(time(15, 20), time(15, 30), "closing")

    daily_entries = []

    for day in days:
        entries = timetable.entries.filter(
            day=day
        ).select_related(
            "subject",
            "teacher",
            "option_group",
        )

        entries_by_period = {}

        for entry in entries:
            period = (entry.start_time, entry.end_time)

            entries_by_period.setdefault(period, []).append(entry)

        cells = []

        for slot in slots:
            period = (slot["start"], slot["end"])

            period_entries = entries_by_period.get(period, [])

            kind = slot["kind"]

            if kind == "morning":
                label = "Assembly" if day == "Monday" else "Devotion"
            elif kind == "break":
                label = "Break"
            elif kind == "lunch":
                label = "Lunch"
            elif kind == "closing":
                label = "Closing / Dismissal"
            else:
                label = ""

            add_url = (
                f"{reverse('timetables:entry_create', args=[timetable.pk])}"
                f"?day={day}"
                f"&start_time={slot['start'].strftime('%H:%M')}"
                f"&end_time={slot['end'].strftime('%H:%M')}"
            )

            cells.append({
                "start": slot["start"],
                "end": slot["end"],
                "kind": kind,
                "label": label,
                "entries": period_entries,
                "add_url": add_url,
            })

        daily_entries.append({
            "name": day,
            "cells": cells,
        })

    other_timetables = Timetable.objects.filter(
        year=timetable.year,
        term=timetable.term
    ).select_related("grade").order_by("grade__name")

    return render(request, "timetables/timetable_detail.html", {
        "timetable": timetable,
        "daily_entries": daily_entries,
        "other_timetables": other_timetables,
    })


@login_required
def timetable_edit(request, pk):
    timetable = get_object_or_404(Timetable, pk=pk)
    form = TimetableForm(request.POST or None, instance=timetable)

    if form.is_valid():
        timetable = form.save()
        messages.success(request, "Timetable updated successfully.")
        return redirect("timetables:timetable_detail", pk=timetable.pk)

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Edit Timetable",
        "cancel_url": reverse("timetables:timetable_detail", args=[pk]),
    })


@login_required
@require_POST
def timetable_delete(request, pk):
    timetable = get_object_or_404(Timetable, pk=pk)
    timetable.delete()
    messages.success(request, "Timetable deleted successfully.")
    return redirect("timetables:timetable_list")



@login_required
def entry_create(request, timetable_pk):
    timetable = get_object_or_404(Timetable, pk=timetable_pk)

    initial = {
        "day": request.GET.get("day", ""),
        "start_time": request.GET.get("start_time", ""),
        "end_time": request.GET.get("end_time", ""),
    }

    formset = TimetableEntryFormSet(
        request.POST or None,
        form_kwargs={"timetable": timetable},
    )

    if request.method != "POST":
        for form in formset.forms:
            form.initial.update(initial)

    if request.method == "POST" and formset.is_valid():
        entries = []

        for form in formset.forms:
            if not form.has_changed():
                continue

            entry = form.save(commit=False)
            entry.timetable = timetable

            try:
                entry.full_clean()
                entries.append((form, entry))

            except ValidationError as error:
                if hasattr(error, "error_dict"):
                    for field, field_errors in error.error_dict.items():
                        if field in form.fields:
                            form.add_error(field, field_errors)
                        else:
                            form.add_error(None, field_errors)
                else:
                    form.add_error(None, error)

        # Check for conflicts between lessons submitted together.
        for i, (form_a, entry_a) in enumerate(entries):
            for form_b, entry_b in entries[i + 1:]:

                if (
                    entry_a.day != entry_b.day
                    or entry_a.start_time >= entry_b.end_time
                    or entry_b.start_time >= entry_a.end_time
                ):
                    continue

                # Whole-class lessons cannot overlap option lessons.
                if (
                    entry_a.activity != "lesson"
                    or entry_b.activity != "lesson"
                    or not entry_a.option_group_id
                    or not entry_b.option_group_id
                ):
                    form_b.add_error(
                        None,
                        "A whole-class activity cannot overlap an option lesson."
                    )

                # The same teacher cannot teach two simultaneous lessons.
                if (
                    entry_a.teacher_id
                    and entry_a.teacher_id == entry_b.teacher_id
                ):
                    form_b.add_error(
                        "teacher",
                        "This teacher cannot teach two lessons at the same time."
                    )

        if entries and all(not form.errors for form, entry in entries):
            try:
                with transaction.atomic():
                    for form, entry in entries:
                        entry.save()

                messages.success(
                    request,
                    f"{len(entries)} timetable lesson(s) added successfully."
                )

                return redirect(
                    "timetables:timetable_detail",
                    pk=timetable.pk
                )

            except ValidationError as error:
                messages.error(request, str(error))

        elif not entries:
            if formset.forms:
                formset.forms[0].add_error(
                    None,
                    "Please enter at least one lesson."
                )

    return render(request, "timetables/form.html", {
        "formset": formset,
        "page_title": f"Add Lessons - {timetable.grade}",
        "cancel_url": reverse(
            "timetables:timetable_detail",
            args=[timetable.pk]
        ),
    })

@login_required
def entry_edit(request, pk):
    entry = get_object_or_404(
        TimetableEntry.objects.select_related("timetable"),
        pk=pk
    )

    form = TimetableEntryForm(
        request.POST or None,
        instance=entry,
        timetable=entry.timetable,
    )

    if form.is_valid():
        updated_entry = form.save(commit=False)
        updated_entry.timetable = entry.timetable

        try:
            updated_entry.full_clean()
            updated_entry.save()
            messages.success(request, "Timetable entry updated successfully.")
            return redirect(
                "timetables:timetable_detail",
                pk=entry.timetable.pk
            )
        except ValidationError as error:
            form.add_error(None, error)

    return render(request, "timetables/form.html", {
        "form": form,
        "page_title": "Edit Timetable Entry",
        "cancel_url": reverse(
            "timetables:timetable_detail",
            args=[entry.timetable.pk]
        ),
    })


@login_required
@require_POST
def entry_delete(request, pk):
    entry = get_object_or_404(TimetableEntry, pk=pk)
    timetable_pk = entry.timetable.pk
    entry.delete()
    messages.success(request, "Timetable entry deleted successfully.")
    return redirect("timetables:timetable_detail", pk=timetable_pk)
