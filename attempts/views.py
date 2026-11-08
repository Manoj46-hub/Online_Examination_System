from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from exams.models import Exam, Question
from .models import ExamAttempt, StudentExamPermission
from .services import create_exam_attempt, evaluate_and_submit_attempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import ExamAttempt, StudentAnswer
from django.utils import timezone
from django.urls import resolve
from datetime import datetime
from django.urls import reverse


@login_required
def start_exam(request):

    if request.user.role != 'STUDENT':
        return redirect('student_login')

    exam_id = request.session.get('verified_exam_id')

    if not exam_id:
        return redirect('exam_verification')

    exam = get_object_or_404(
        Exam,
        id=exam_id,
        is_active=True
    )

    permission = StudentExamPermission.objects.filter(
        student=request.user,
        exam=exam
    ).first()

    if not permission or not permission.is_enabled:
        messages.error(
            request,
            'You do not have permission to access this examination.'
        )
        return redirect('student_dashboard')

    start_datetime = timezone.make_aware(
        datetime.combine(exam.exam_date, exam.start_time)
    )

    end_datetime = timezone.make_aware(
        datetime.combine(exam.exam_date, exam.end_time)
    )

    current_time = timezone.now()

    if current_time < start_datetime:
        messages.warning(
            request,
            'The examination has not started yet.'
        )
        return redirect('exam_instructions')

    if current_time >= end_datetime:
        messages.error(
            request,
            'The examination time has ended.'
        )
        return redirect('student_dashboard')

    try:
        attempt = create_exam_attempt(
            student=request.user,
            exam=exam,
            access_version=permission.access_version
        )

        # Ensure the attempt uses the common exam end time
        if attempt.end_time != end_datetime:
            attempt.end_time = end_datetime
            attempt.save(update_fields=['end_time'])

    except ValidationError as error:
        messages.error(request, str(error))
        return redirect('exam_instructions')

    return redirect(
        'exam_question',
        attempt_id=attempt.id,
        question_number=1
    )

@login_required
def exam_question(request, attempt_id, question_number):

    if request.user.role != 'STUDENT':
        return redirect('student_login')

    attempt = get_object_or_404(
        ExamAttempt,
        id=attempt_id,
        student=request.user
    )

    if attempt.status != 'IN_PROGRESS':
        messages.info(request, 'This examination has already been submitted.')
        return redirect('student_dashboard')

    if timezone.now() >= attempt.end_time:
        messages.error(
            request,
            'Examination time is over. You cannot answer any more questions.'
        )
        return redirect('student_dashboard')

    question_ids = attempt.question_order

    if question_number < 1 or question_number > len(question_ids):
        from django.http import Http404
        raise Http404("Question not found")

    question_id = question_ids[question_number - 1]

    question = get_object_or_404(
        Question,
        id=question_id
    )
    print("DEBUG: Question found:", question.id)

    answer = attempt.answers.get(question=question)
    print("DEBUG: Answer found:", answer.id)
    original_order = attempt.option_orders[str(question.id)]

    options = []

    for index, original_label in enumerate(original_order):

        option_text = getattr(
            question,
            f'option_{original_label.lower()}'
        )

        display_label = chr(65 + index)

        options.append({
            'label': display_label,
            'text': option_text,
        })

    answer_map = {
        item.question_id: item
        for item in attempt.answers.all()
    }

    palette_statuses = []

    for qid in question_ids:
        item = answer_map.get(qid)

        if item and item.is_marked:
            status = 'marked'
        elif item and item.is_answered:
            status = 'answered'
        else:
            status = 'not-visited'

        palette_statuses.append(status)
    question_numbers = range(1, len(question_ids) + 1)

    palette_items = []

    for index, number in enumerate(question_numbers):
        palette_items.append({
            'number': number,
            'status': palette_statuses[index],
        })

    context = {
        'attempt': attempt,
        'question': question,
        'question_number': question_number,
        'total_questions': len(question_ids),
        'options': options,
        'answer': answer,
        'palette_items': palette_items,
        'palette_statuses': palette_statuses,
        'question_numbers': range(1, len(question_ids) + 1),
    }

    return render(
        request,
        'attempts/exam_question.html',
        context
    )

@login_required
@require_POST
def save_answer(request, attempt_id):

    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    attempt = get_object_or_404(
        ExamAttempt,
        id=attempt_id,
        student=request.user
    )

    if attempt.status != 'IN_PROGRESS':
        return JsonResponse({'error': 'Exam already submitted'}, status=400)

    if timezone.now() >= attempt.end_time:
        return JsonResponse({'error': 'Exam time is over'}, status=400)

    question_id = request.POST.get('question_id')
    selected_answer = request.POST.get('selected_answer')

    if selected_answer not in ['A', 'B', 'C', 'D']:
        return JsonResponse({'error': 'Invalid answer'}, status=400)

    if str(question_id) not in [str(qid) for qid in attempt.question_order]:
        return JsonResponse({'error': 'Invalid question'}, status=400)

    answer = get_object_or_404(
        StudentAnswer,
        attempt=attempt,
        question_id=question_id
    )

    answer.selected_answer = selected_answer
    answer.is_answered = True
    answer.save()

    return JsonResponse({
        'success': True,
        'message': 'Answer saved successfully'
    })

@login_required
@require_POST
def clear_answer(request, attempt_id):

    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    attempt = get_object_or_404(
        ExamAttempt,
        id=attempt_id,
        student=request.user
    )

    if attempt.status != 'IN_PROGRESS':
        return JsonResponse({'error': 'Exam already submitted'}, status=400)

    if timezone.now() >= attempt.end_time:
        return JsonResponse({'error': 'Exam time is over'}, status=400)

    question_id = request.POST.get('question_id')

    if str(question_id) not in [str(qid) for qid in attempt.question_order]:
        return JsonResponse({'error': 'Invalid question'}, status=400)

    answer = get_object_or_404(
        StudentAnswer,
        attempt=attempt,
        question_id=question_id
    )

    answer.selected_answer = ''
    answer.is_answered = False
    answer.save()

    return JsonResponse({'success': True})
@login_required
@require_POST
def mark_for_review(request, attempt_id):

    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    attempt = get_object_or_404(
        ExamAttempt,
        id=attempt_id,
        student=request.user
    )

    if attempt.status != 'IN_PROGRESS':
        return JsonResponse({'error': 'Exam already submitted'}, status=400)

    if timezone.now() >= attempt.end_time:
        return JsonResponse({'error': 'Exam time is over'}, status=400)

    question_id = request.POST.get('question_id')

    if str(question_id) not in [str(qid) for qid in attempt.question_order]:
        return JsonResponse({'error': 'Invalid question'}, status=400)

    answer = get_object_or_404(
        StudentAnswer,
        attempt=attempt,
        question_id=question_id
    )

    selected_answer = request.POST.get('selected_answer', '')

    if selected_answer:
        if selected_answer not in ['A', 'B', 'C', 'D']:
            return JsonResponse({'error': 'Invalid answer'}, status=400)

        answer.selected_answer = selected_answer
        answer.is_answered = True

    answer.is_marked = True
    answer.save()

    return JsonResponse({
        'success': True,
        'message': 'Question marked for review'
    })



@login_required
@require_POST
def submit_exam(request, attempt_id):

    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    attempt = get_object_or_404(
        ExamAttempt,
        id=attempt_id,
        student=request.user
    )

    if attempt.status == 'SUBMITTED':
        return JsonResponse({
            'success': True,
            'message': 'Exam already submitted',
            'redirect_url': reverse(
                'exam_result',
                kwargs={'attempt_id': attempt.id}
            )
        })

    if timezone.now() >= attempt.end_time:
        attempt = evaluate_and_submit_attempt(attempt)
        return JsonResponse({
            'success': True,
            'message': 'Exam time ended. Your exam was submitted.',
            'score': attempt.score,
            'redirect_url': reverse(
                'exam_result',
                kwargs={'attempt_id': attempt.id}
            )
        })

    attempt = evaluate_and_submit_attempt(attempt)

    return JsonResponse({
        'success': True,
        'message': 'Exam submitted successfully',
        'score': attempt.score,
        'redirect_url': reverse(
            'exam_result',
            kwargs={'attempt_id': attempt.id}
        )
    })

@login_required
def exam_result(request, attempt_id):

    if request.user.role != 'STUDENT':
        return redirect('student_login')

    attempt = get_object_or_404(
        ExamAttempt,
        id=attempt_id,
        student=request.user,
        status='SUBMITTED'
    )

    answers = attempt.answers.select_related('question').all()

    total_questions = answers.count()
    correct_answers = 0
    answered_questions = 0

    for answer in answers:

        if not answer.is_answered:
            continue

        answered_questions += 1

        question = answer.question
        option_order = attempt.option_orders[str(question.id)]

        displayed_index = ord(answer.selected_answer) - ord('A')

        if 0 <= displayed_index < len(option_order):
            original_answer = option_order[displayed_index]

            if original_answer == question.correct_answer:
                correct_answers += 1

    wrong_answers = answered_questions - correct_answers
    unanswered_questions = total_questions - answered_questions

    context = {
        'attempt': attempt,
        'exam': attempt.exam,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'wrong_answers': wrong_answers,
        'unanswered_questions': unanswered_questions,
        'score': attempt.score,
    }

    return render(
        request,
        'attempts/exam_result.html',
        context
    )

@login_required
@require_POST
def auto_submit_exam(request, attempt_id):

    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    attempt = get_object_or_404(
        ExamAttempt,
        id=attempt_id,
        student=request.user
    )

    if timezone.now() < attempt.end_time:
        return JsonResponse({
            'error': 'Exam deadline has not arrived'
        }, status=400)

    attempt = evaluate_and_submit_attempt(attempt)

    return JsonResponse({
        'success': True,
        'message': 'Exam automatically submitted',
        'score': attempt.score,
        'redirect_url': reverse(
            'exam_result',
            kwargs={'attempt_id': attempt.id}
        )
    })

