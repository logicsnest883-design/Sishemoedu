from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("enter-scores/<int:test_id>/", views.enter_scores_grid, name="enter_scores"),
    path("tests/", views.view_tests, name="view_tests"),
    path("enter-scores/", views.enter_scores_list, name="enter_scores_list"),
    path("enter-scores/<str:test_type>/", views.enter_scores_grid, name="enter_scores"),
    path("class-register/", views.class_register, name="class_register"),

]
