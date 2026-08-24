from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.home, name="home"),

    # Section URLs
    path("sections/<int:section_id>/", views.section_detail, name="section_detail"),
    path("sections/<int:section_id>/subjects/", views.section_subjects, name="section_subjects"),
    path("sections/<int:section_id>/books/", views.section_books, name="section_books"),
    path("sections/<int:section_id>/notes/", views.section_notes, name="section_notes"),
    path("sections/<int:section_id>/tutorials/", views.section_tutorials, name="section_tutorials"),
    path("sections/<int:section_id>/grades/", views.section_grades, name="section_grades"),

    # Grade → Subjects
    path("<str:mode>/grade/<int:grade_id>/subjects/", views.grade_subjects, name="grade_subjects"),

    # Topics
    path("subjects/<int:subject_id>/grade/<int:grade_id>/topics/", views.subject_topics, name="subject_topics"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),

    # Notes
    path("topics/<int:topic_id>/notes/", views.topic_notes, name="topic_notes"),
    path('section/<int:section_id>/comprehension/', views.section_comprehension, name='section_comprehension'),
    path("comprehension/<int:section_id>/grades/", views.grade_comprehension, name="grade_comprehension"),
    path("comprehension/grade/<int:grade_id>/", views.grade_comprehension_list, name="grade_comprehension"),
    path(
    "comprehension/grade/<int:grade_id>/<slug:slug>/",
    views.read_comprehension,
    name="read_comprehension"
),



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
