
import uuid
from django.db import models


class QuizStage(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    competition = models.ForeignKey(
        'QuizCompetition',
        on_delete=models.CASCADE,
        related_name='stages'
    )

    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=150, blank=True)
    category = models.CharField(max_length=100, blank=True)

    duration_seconds = models.PositiveSmallIntegerField(
        default=300,
        editable=False
    )

    question_seconds = models.PositiveSmallIntegerField(
        default=30,
        editable=False
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending'
    )

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['number']
        constraints = [
            models.UniqueConstraint(
                fields=['competition', 'number'],
                name='unique_quiz_stage_number'
            )
        ]

    def __str__(self):
        return f"{self.competition} - Stage {self.number}"


class QuizCompetition(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('live', 'Live'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(
        max_length=200,
        default="Sishemo Graduation Quiz"
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='draft'
    )

    current_stage = models.ForeignKey(
        QuizStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_for_competitions'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class QuizQuestion(models.Model):
    OPTION_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]

    stage = models.ForeignKey(
        QuizStage,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    order = models.PositiveSmallIntegerField()
    question_text = models.TextField()

    options = models.JSONField(default=list)

    correct_option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES
    )

    points = models.PositiveSmallIntegerField(default=10)

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(
                fields=['stage', 'order'],
                name='unique_quiz_question_order'
            )
        ]

    def __str__(self):
        return f"Stage {self.stage.number} - Question {self.order}"


class QuizParticipant(models.Model):
    competition = models.ForeignKey(
        QuizCompetition,
        on_delete=models.CASCADE,
        related_name='participants'
    )

    name = models.CharField(max_length=150)

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    total_score = models.PositiveIntegerField(default=0)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-total_score', 'joined_at']

    def __str__(self):
        return self.name


class QuizAnswer(models.Model):
    participant = models.ForeignKey(
        QuizParticipant,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    selected_option = models.CharField(
        max_length=1,
        choices=QuizQuestion.OPTION_CHOICES
    )

    is_correct = models.BooleanField(default=False)

    points_awarded = models.PositiveSmallIntegerField(default=0)

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['participant', 'question'],
                name='unique_participant_question_answer'
            )
        ]

    def __str__(self):
        return f"{self.participant.name} - {self.question}"
