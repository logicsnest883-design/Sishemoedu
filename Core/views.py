from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Section, Subject, Topic, Note, Grade

# Create your views here.
# school/views.py
from django.shortcuts import render

def home(request):
    sections = Section.objects.all()  # Will give Lower, Upper, Secondary
    return render(request, "frontpage.html", {"sections": sections})

def section_grades(request, section_id):
    section = get_object_or_404(Section, id=section_id)

    # Order grades alphabetically
    grades = section.grades.all().order_by("name")

    return render(
        request,
        "section_grades.html",
        {
            "section": section,
            "grades": grades,
            "mode": "notes",
        },
    )


def grade_subjects(request, grade_id, mode):
    grade = get_object_or_404(Grade, id=grade_id)

    # Subjects still belong to section
    subjects = Subject.objects.filter(section=grade.section)

    return render(request, "grade_subjects.html", {
        "grade": grade,
        "subjects": subjects,
        "mode": mode,
    })



def subject_books(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    books = subject.books.all()
    return render(request, "subject_books.html", {"subject": subject, "books": books})



def about(request):
    return render(request, "about.html")



from django.contrib import messages

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        # For now just show success message
        messages.success(request, "Your message has been sent successfully!")

    return render(request, "contact.html")


def section_subjects(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    subjects = section.subjects.all()
    return render(request, "section_subjects.html", {"section": section, "subjects": subjects})


def subject_topics(request, subject_id, grade_id):
    subject = get_object_or_404(Subject, id=subject_id)

    topics = subject.topics.filter(grade_id=grade_id).order_by("order")

    return render(request, "subject_topics.html", {
        "subject": subject,
        "topics": topics,
        "grade_id": grade_id
    })



def topic_notes(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    notes = topic.notes.all()
    return render(request, "topic_notes.html", {"topic": topic, "notes": notes})


def section_detail(request, section_id):
    section = get_object_or_404(Section, id=section_id)

    grades = section.grades.all().order_by("name")

    return render(
        request,
        "section_detail.html",
        {
            "section": section,
            "grades": grades,
        },
    )




def section_notes(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    grades = section.grades.all()
    return render(request, "section_grades.html", {
        "section": section,
        "grades": grades,
        "mode": "notes"
    })


def section_books(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    grades = section.grades.all()
    return render(request, "section_grades.html", {
        "section": section,
        "grades": grades,
        "mode": "books"
    })



def section_tutorials(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    tutorials = Tutorial.objects.filter(section=section)
    return render(request, "section_tutorials.html", {"section": section, "tutorials": tutorials})

from django.shortcuts import render, get_object_or_404
from .models import Section, Grade

def section_comprehension(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    grades = Grade.objects.filter(section=section)

    context = {
        'section': section,
        'grades': grades
    }
    return render(request, 'comprehension_grade.html', context)

from django.shortcuts import render, get_object_or_404
from .models import Section, Grade

def grade_comprehension(request, section_id):
    # Get the section (Lower Primary, Upper Primary, Secondary)
    section = get_object_or_404(Section, id=section_id)

    # Filter all grades that belong to this section
    grades = Grade.objects.filter(section=section).order_by("name")

    context = {
        "section": section,
        "grades": grades
    }

    return render(request, "grades_comprehension.html", context)

from django.shortcuts import render, get_object_or_404
from .models import Grade, Comprehension

def grade_comprehension_list(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)
    comprehensions = Comprehension.objects.filter(grade=grade)

    context = {
        "grade": grade,
        "comprehensions": comprehensions
    }
    return render(request, "grade_comprehension_list.html", context)


from django.shortcuts import render, get_object_or_404
from .models import Comprehension

def read_comprehension(request, grade_id, slug):
    comprehension = get_object_or_404(Comprehension, grade_id=grade_id, slug=slug)

    context = {
        "comp": comprehension
    }
    return render(request, "read_comprehension.html", context)

# The magic Forest
#