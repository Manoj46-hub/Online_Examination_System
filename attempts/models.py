
import uuid

from django.db import models
from django.conf import settings
from exams.models import Exam, Question


class ExamAttempt(models.Model):

    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_attempts'
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='attempts'
    )

    started_at = models.DateTimeField(auto_now_add=True)

    end_time = models.DateTimeField()

    submitted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_PROGRESS'
    )

    score = models.PositiveIntegerField(
        default=0
    )

    question_order = models.JSONField(default=list)

    option_orders = models.JSONField(default=dict)
    access_version = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'exam'],
                condition=models.Q(status='IN_PROGRESS'),
                name='one_active_attempt_per_student_exam'
            )
        ]

    def __str__(self):
        return f"{self.student.name} - {self.exam.title}"


class StudentAnswer(models.Model):

    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    selected_answer = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
        ],
        blank=True,
        default=''
    )

    is_answered = models.BooleanField(default=False)

    is_marked = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['attempt', 'question'],
                name='unique_question_per_attempt'
            )
        ]

    def __str__(self):
        return f"{self.attempt.student.name} - Question {self.question.id}"

class StudentExamPermission(models.Model):

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_permissions'
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='student_permissions'
    )

    is_enabled = models.BooleanField(default=False)
    access_version = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'exam'],
                name='unique_student_exam_permission'
            )
        ]

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"

class ExamResult(ExamAttempt):

    class Meta:
        proxy = True
        verbose_name = 'Exam Result'
        verbose_name_plural = 'Exam Results'