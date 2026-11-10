from django.test import TestCase
import random

from django.test import TestCase
from django.core.exceptions import ValidationError

from exams.models import Question
from .services import select_exam_questions


class DynamicQuestionSelectionTest(TestCase):

    def setUp(self):
        for i in range(60):
            Question.objects.create(
                unit=f'UNIT_{(i % 5) + 1}',
                topic=f'Topic {i}',
                question_text=f'Question {i}',
                option_a='Option A',
                option_b='Option B',
                option_c='Option C',
                option_d='Option D',
                correct_answer='A',
                explanation='Test explanation',
                difficulty='EASY'
            )

    def test_selects_exactly_50_questions(self):
        selected = select_exam_questions()

        self.assertEqual(len(selected), 50)
        self.assertEqual(len(set(q.id for q in selected)), 50)

    def test_works_with_more_than_500_questions(self):
        for i in range(60, 550):
            Question.objects.create(
                unit=f'UNIT_{(i % 5) + 1}',
                topic=f'Topic {i}',
                question_text=f'Question {i}',
                option_a='Option A',
                option_b='Option B',
                option_c='Option C',
                option_d='Option D',
                correct_answer='A',
                explanation='Test explanation',
                difficulty='EASY'
            )

        selected = select_exam_questions()
        self.assertEqual(len(selected), 50)

    def test_requires_at_least_50_questions(self):
        Question.objects.all().delete()

        with self.assertRaises(ValidationError):
            select_exam_questions()