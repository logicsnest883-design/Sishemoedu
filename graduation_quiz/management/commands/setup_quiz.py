
from django.core.management.base import BaseCommand
from django.db import transaction

from graduation_quiz.models import QuizCompetition, QuizStage


class Command(BaseCommand):
    help = "Create the Sishemo Graduation Quiz and its five stages"

    @transaction.atomic
    def handle(self, *args, **options):

        competition, created = QuizCompetition.objects.get_or_create(
            title="Sishemo Graduation Quiz",
            defaults={
                "status": "draft",
            }
        )

        for number in range(1, 6):
            QuizStage.objects.get_or_create(
                competition=competition,
                number=number,
                defaults={
                    "title": f"Stage {number}",
                    "duration_seconds": 300,
                    "question_seconds": 30,
                    "status": "pending",
                }
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Quiz competition and five stages are ready."
            )
        )
