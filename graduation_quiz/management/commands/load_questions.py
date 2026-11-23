
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from graduation_quiz.models import (
    QuizCompetition,
    QuizStage,
    QuizQuestion,
    QuizAnswer,
)


class Command(BaseCommand):
    help = "Load or replace the graduation quiz questions"

    @transaction.atomic
    def handle(self, *args, **options):

        file_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "question_bank.json"
        )

        if not file_path.exists():
            raise CommandError("question_bank.json was not found.")

        try:
            with open(file_path, encoding="utf-8") as file:
                bank = json.load(file)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON: {exc}")

        competition = QuizCompetition.objects.filter(
            title="Sishemo Graduation Quiz"
        ).order_by("-created_at").first()

        if not competition:
            raise CommandError(
                "Run python manage.py setup_quiz first."
            )

        if QuizAnswer.objects.filter(
            question__stage__competition=competition
        ).exists():
            raise CommandError(
                "Answers already exist. Restart the tournament first "
                "before replacing questions."
            )

        stages = {
            stage.number: stage
            for stage in QuizStage.objects.filter(
                competition=competition
            )
        }

        if len(stages) != 5:
            raise CommandError("The five quiz stages have not been created.")

        questions_to_create = []

        for number in range(1, 6):

            stage_data = bank.get(str(number))

            if not stage_data:
                raise CommandError(f"Stage {number} is missing.")

            questions = stage_data.get("questions", [])

            if len(questions) != 20:
                raise CommandError(
                    f"Stage {number} must have exactly 20 questions."
                )

            for index, item in enumerate(questions, start=1):

                options = item.get("options", {})
                correct = item.get("correct_option")

                if not item.get("question"):
                    raise CommandError(
                        f"Stage {number}, question {index} is missing text."
                    )

                if set(options.keys()) != {"A", "B", "C", "D"}:
                    raise CommandError(
                        f"Stage {number}, question {index} needs options A-D."
                    )

                if not all(options.values()):
                    raise CommandError(
                        f"Stage {number}, question {index} has an empty option."
                    )

                if correct not in ["A", "B", "C", "D"]:
                    raise CommandError(
                        f"Stage {number}, question {index} has an invalid answer."
                    )

                questions_to_create.append(
                    QuizQuestion(
                        stage=stages[number],
                        order=index,
                        question_text=item["question"],
                        options=options,
                        correct_option=correct,
                        points=item.get("points", 10),
                    )
                )

            stage = stages[number]
            stage.title = stage_data.get("title", f"Stage {number}")
            stage.category = stage_data.get("category", "")
            stage.save(update_fields=["title", "category"])

        QuizQuestion.objects.filter(
            stage__competition=competition
        ).delete()

        QuizQuestion.objects.bulk_create(questions_to_create)

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully replaced the questions with 100 questions."
            )
        )
