
from django.urls import path
from . import views

app_name = 'graduation_quiz'

urlpatterns = [
    path('', views.quiz_home, name='home'),

    path('play/', views.quiz_play, name='play'),

    path('status/', views.quiz_status, name='status'),

    path('submit/', views.submit_answer, name='submit'),

    path('leaderboard/', views.leaderboard_page, name='leaderboard'),

    path('leaderboard/data/', views.quiz_leaderboard, name='leaderboard_data'),

    path('results/', views.quiz_results, name='results'),
    path('control/', views.quiz_control, name='control'),
    path('reset/', views.reset_quiz, name='reset'),
]
