
from django.contrib import admin
from .models import Exam, Question
from django.contrib.auth import get_user_model
from attempts.models import StudentExamPermission

User = get_user_model()

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'exam_date',
        'start_time',
        'end_time',
        'verification_code',
        'is_active',
        'created_at',
    )

    

    list_filter = ('exam_date', 'is_active')

    search_fields = ('title', 'verification_code')

    actions = [
        'enable_all_students',
        'disable_all_students',
    ]


    @admin.action(description='Enable access for all students')
    def enable_all_students(self, request, queryset):

        students = User.objects.filter(role='STUDENT')

        for exam in queryset:
            for student in students:

                permission, created = StudentExamPermission.objects.get_or_create(
                    student=student,
                    exam=exam,
                    defaults={
                        'is_enabled': True,
                        'access_version': 1,
                    }
                )

                if not created and not permission.is_enabled:
                    permission.is_enabled = True
                    permission.access_version += 1

                    permission.save(
                        update_fields=['is_enabled', 'access_version', 'updated_at']
                    )

        self.message_user(
            request,
            'Exam access enabled for all students.'
        )

    @admin.action(description='Disable access for all students')
    def disable_all_students(self, request, queryset):

        for exam in queryset:
            StudentExamPermission.objects.filter(
                exam=exam
            ).update(is_enabled=False)

        self.message_user(
            request,
            'Exam access disabled for all students.'
        )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'unit',
        'topic',
        'difficulty',
        'correct_answer',
    )

    list_filter = (
        'unit',
        'difficulty',
    )

    search_fields = (
        'question_text',
        'topic',
    )
    list_per_page = 25
