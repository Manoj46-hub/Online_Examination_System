from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_login, name='home'),
    path('student-login/', views.student_login, name='student_login'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('verify-exam/', views.exam_verification, name='exam_verification'),
    path('exam-instructions/', views.exam_instructions, name='exam_instructions'),
]