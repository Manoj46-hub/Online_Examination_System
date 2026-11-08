
from django.db import models



from django.db import models


class Exam(models.Model):
    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    exam_date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    verification_code = models.CharField(max_length=20)

    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class Question(models.Model):

    UNIT_CHOICES = [
        ('UNIT_1', 'Unit I'),
        ('UNIT_2', 'Unit II'),
        ('UNIT_3', 'Unit III'),
        ('UNIT_4', 'Unit IV'),
        ('UNIT_5', 'Unit V'),
    ]

    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    ]

    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES
    )

    topic = models.CharField(max_length=150)

    question_text = models.TextField()

    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)

    correct_answer = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
        ]
    )

    explanation = models.TextField()

    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='MEDIUM'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.unit} - {self.topic}"
