
from django.contrib import admin, messages
from django.utils import timezone
from django.db import transaction

from .models import (
    QuizCompetition,
    QuizStage,
    QuizQuestion,
    QuizParticipant,
    QuizAnswer,
)


@admin.action(description="Open parent registration")
def open_registration(modeladmin, request, queryset):
    updated = queryset.filter(status='draft').update(status='ready')

    modeladmin.message_user(
        request,
        f"Registration opened for {updated} competition(s).",
        messages.SUCCESS,
    )


@admin.action(description="Activate selected stage")
def activate_stage(modeladmin, request, queryset):

    if queryset.count() != 1:
        modeladmin.message_user(
            request,
            "Select exactly one stage.",
            messages.ERROR,
        )
        return

    stage = queryset.first()

    with transaction.atomic():
        competition = QuizCompetition.objects.select_for_update().get(
            pk=stage.competition_id
        )

        stage = QuizStage.objects.select_for_update().get(pk=stage.pk)

        if competition.status == 'completed':
            modeladmin.message_user(
                request,
                "This competition has already finished.",
                messages.ERROR,
            )
            return

        if stage.status != 'pending':
            modeladmin.message_user(
                request,
                "Only pending stages can be activated.",
                messages.ERROR,
            )
            return

        if stage.questions.count() != 10:
            modeladmin.message_user(
                request,
                "This stage needs exactly 10 questions.",
                messages.ERROR,
            )
            return

        if QuizStage.objects.filter(
            competition=competition,
            status='active',
        ).exists():
            modeladmin.message_user(
                request,
                "Complete the current stage before activating another.",
                messages.ERROR,
            )
            return

        previous_stages = QuizStage.objects.filter(
            competition=competition,
            number__lt=stage.number,
        )

        if previous_stages.exclude(status='completed').exists():
            modeladmin.message_user(
                request,
                "Activate stages in order. Complete the previous stages first.",
                messages.ERROR,
            )
            return

        stage.status = 'active'
        stage.started_at = timezone.now()
        stage.save(update_fields=['status', 'started_at'])

        competition.current_stage = stage
        competition.status = 'live'

        if not competition.started_at:
            competition.started_at = timezone.now()

        competition.save(update_fields=[
            'current_stage',
            'status',
            'started_at',
        ])

    modeladmin.message_user(
        request,
        f"Stage {stage.number} has been activated.",
        messages.SUCCESS,
    )


@admin.register(QuizCompetition)
class QuizCompetitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'current_stage', 'created_at')
    list_filter = ('status',)
    actions = [open_registration]


@admin.register(QuizStage)
class QuizStageAdmin(admin.ModelAdmin):
    list_display = (
        'competition',
        'number',
        'title',
        'category',
        'status',
        'started_at',
    )
    list_filter = ('status', 'competition')
    actions = [activate_stage]
    readonly_fields = (
        'started_at',
        'completed_at',
    )


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('stage', 'order', 'question_text', 'points')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(QuizParticipant)
class QuizParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'competition', 'total_score', 'joined_at')
    search_fields = ('name',)
    list_filter = ('competition',)


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'participant',
        'question',
        'selected_option',
        'is_correct',
        'points_awarded',
    )
    readonly_fields = (
        'participant',
        'question',
        'selected_option',
        'is_correct',
        'points_awarded',
        'submitted_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
