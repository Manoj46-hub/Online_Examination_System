
from django.contrib import admin
from .models import ExamAttempt, ExamResult, StudentAnswer, StudentExamPermission
from django.db.models import OuterRef, Subquery, F
class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    readonly_fields = (
        'question',
        'selected_answer',
        'is_answered',
        'is_marked',
    )


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'exam',
        'started_at',
        'end_time',
        'submitted_at',
        'status',
        'score',
    )

    list_filter = (
        'status',
        'exam',
    )

    search_fields = (
        'student__name',
        'student__username',
        'exam__title',
    )

    readonly_fields = (
        'started_at',
        'submitted_at',
        'question_order',
        'option_orders',
        'score',
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        latest_attempt = ExamAttempt.objects.filter(
            student=OuterRef('student'),
            exam=OuterRef('exam'),
            status='SUBMITTED'
        ).order_by(
            '-submitted_at',
            '-started_at'
        ).values('pk')[:1]

        return queryset.filter(
            status='SUBMITTED'
        ).annotate(
            latest_attempt_id=Subquery(latest_attempt)
        ).filter(
            pk=F('latest_attempt_id')
        )

    inlines = [StudentAnswerInline]


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):

    list_display = (
        'attempt',
        'question',
        'selected_answer',
        'is_answered',
        'is_marked',
    )

    list_filter = (
        'is_answered',
        'is_marked',
    )

@admin.register(StudentExamPermission)
class StudentExamPermissionAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'exam',
        'is_enabled',
        'access_version',
        'updated_at',
    )

    list_filter = ('is_enabled', 'exam')

    search_fields = (
        'student__name',
        'student__username',
        'exam__title',
    )

    readonly_fields = ('access_version', 'updated_at')

    actions = ['enable_access', 'disable_access']

    @admin.action(description='Enable access for selected students')
    def enable_access(self, request, queryset):

        for permission in queryset:
            if not permission.is_enabled:
                permission.is_enabled = True
                permission.access_version += 1
                permission.save()

        self.message_user(
            request,
            'Access enabled for selected students.'
        )

    @admin.action(description='Disable access for selected students')
    def disable_access(self, request, queryset):

        queryset.update(is_enabled=False)

        self.message_user(
            request,
            'Access disabled for selected students.'
        )


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'exam',
        'score',
        'correct_answers',
        'wrong_answers',
        'unanswered_questions',
        'status',
        'submitted_at',
    )

    list_filter = (
        'exam',
        'status',
    )

    search_fields = (
        'student__name',
        'student__username',
        'exam__title',
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        latest_attempt = ExamAttempt.objects.filter(
            student=OuterRef('student'),
            exam=OuterRef('exam'),
            status='SUBMITTED'
        ).order_by(
            '-submitted_at',
            '-started_at'
        ).values('pk')[:1]

        return queryset.filter(
            status='SUBMITTED',
            pk=Subquery(latest_attempt)
        ).select_related(
            'student', 'exam'
        ).prefetch_related(
            'answers__question'
        )
    
    def get_answer_stats(self, obj):
        if hasattr(obj, '_answer_stats_cache'):
            return obj._answer_stats_cache

        correct = 0
        wrong = 0
        unanswered = 0

        for answer in obj.answers.all():

            if not answer.is_answered:
                unanswered += 1
                continue

            option_order = obj.option_orders.get(
                str(answer.question_id), []
            )

            if answer.selected_answer:
                index = ord(answer.selected_answer) - ord('A')
            else:
                index = -1

            if (
                0 <= index < len(option_order)
                and option_order[index] == answer.question.correct_answer
            ):
                correct += 1
            else:
                wrong += 1

        obj._answer_stats_cache = (correct, wrong, unanswered)
        return obj._answer_stats_cache


    @admin.display(description='Right Answers')
    def correct_answers(self, obj):
        return self.get_answer_stats(obj)[0]


    @admin.display(description='Wrong Answers')
    def wrong_answers(self, obj):
        return self.get_answer_stats(obj)[1]


    @admin.display(description='Unanswered')
    def unanswered_questions(self, obj):
        return self.get_answer_stats(obj)[2]