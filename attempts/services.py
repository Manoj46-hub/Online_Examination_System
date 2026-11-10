
import random
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from exams.models import Question
from .models import ExamAttempt, StudentAnswer

def select_exam_questions():

    questions = list(Question.objects.all())

    if len(questions) < 50:
        raise ValidationError(
            f'Only {len(questions)} questions are available. '
            'At least 50 are required.'
        )

    selected_questions = random.sample(questions, 50)

    return selected_questions


def generate_option_orders(questions):

    option_orders = {}

    for question in questions:

        options = ['A', 'B', 'C', 'D']
        random.shuffle(options)

        option_orders[str(question.id)] = options

    return option_orders


def create_exam_attempt(student, exam, access_version=0):

    with transaction.atomic():

        existing_attempts = ExamAttempt.objects.select_for_update().filter(
            student=student,
            exam=exam
        ).order_by('-started_at')

        # Prevent multiple attempts during the same access cycle
        same_cycle_attempt = existing_attempts.filter(
            access_version=access_version
        ).first()

        if same_cycle_attempt:
            if same_cycle_attempt.status == 'IN_PROGRESS':
                return same_cycle_attempt

            raise ValidationError(
                'You have already attempted this exam during this access cycle.'
            )

        # Finalize any unfinished attempt from an older access cycle
        old_attempts = existing_attempts.filter(status='IN_PROGRESS')

        for old_attempt in old_attempts:
            evaluate_and_submit_attempt(old_attempt)

        # Select 10 questions from each unit
        questions = select_exam_questions()

        # Randomize options for each question
        option_orders = generate_option_orders(questions)

        # Use the common admin-configured exam deadline
        end_datetime = timezone.make_aware(
            datetime.combine(exam.exam_date, exam.end_time)
        )

        if timezone.now() >= end_datetime:
            raise ValidationError('The examination time has ended.')

        attempt = ExamAttempt.objects.create(
            student=student,
            exam=exam,
            end_time=end_datetime,
            question_order=[question.id for question in questions],
            option_orders=option_orders,
            access_version=access_version
        )

        answers = [
            StudentAnswer(
                attempt=attempt,
                question=question
            )
            for question in questions
        ]

        StudentAnswer.objects.bulk_create(answers)

        return attempt
        
def evaluate_and_submit_attempt(attempt):

    with transaction.atomic():

        attempt = ExamAttempt.objects.select_for_update().get(
            id=attempt.id
        )

        # Prevent duplicate evaluation
        if attempt.status == 'SUBMITTED':
            return attempt

        score = 0

        answers = attempt.answers.select_related('question').all()

        for answer in answers:

            if not answer.is_answered:
                continue

            question = answer.question

            # Get the shuffled option order
            option_order = attempt.option_orders[str(question.id)]

            # Convert displayed answer into original option label
            displayed_index = ord(answer.selected_answer) - ord('A')

            if 0 <= displayed_index < len(option_order):

                original_answer = option_order[displayed_index]

                if original_answer == question.correct_answer:
                    score += 1

        attempt.score = score
        attempt.status = 'SUBMITTED'
        attempt.submitted_at = timezone.now()

        attempt.save(update_fields=[
            'score',
            'status',
            'submitted_at'
        ])

        return attempt
