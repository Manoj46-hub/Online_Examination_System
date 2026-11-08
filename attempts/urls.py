from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_exam, name='start_exam'),
    path(
        '<uuid:attempt_id>/question/<int:question_number>/',
        views.exam_question,
        name='exam_question'
    ),
    path(
        '<uuid:attempt_id>/save-answer/',
        views.save_answer,
        name='save_answer'
    ),
    path(
        '<uuid:attempt_id>/clear-answer/',
        views.clear_answer,
        name='clear_answer'
    ),
    path(
        '<uuid:attempt_id>/mark-review/',
        views.mark_for_review,
        name='mark_for_review'
    ),
    path(
        '<uuid:attempt_id>/submit/',
        views.submit_exam,
        name='submit_exam'
    ),
    path(
        '<uuid:attempt_id>/auto-submit/',
        views.auto_submit_exam,
        name='auto_submit_exam'
    ),
    path(
        '<uuid:attempt_id>/result/',
        views.exam_result,
        name='exam_result'
    ),

]
