from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    first_name = None
    last_name = None

    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('STUDENT', 'Student'),
    ]

    name = models.CharField(max_length=150)

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='STUDENT'
    )

    def __str__(self):
        return f"{self.name} ({self.username})"