
import json
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import F
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

from .models import (
    QuizCompetition,
    QuizParticipant,
    QuizStage,
    QuizQuestion,
    QuizAnswer,
)


QUESTIONS_PER_STAGE = 20
QUESTION_SECONDS = 25

def ensure_quiz_setup():
    stage_categories = [
        (1, "Stage 1", "Riddles"),
        (2, "Stage 2", "Proverbs"),
        (3, "Stage 3", "Philosophy"),
        (4, "Stage 4", "General Knowledge"),
        (5, "Stage 5", "Zambian History"),
    ]

    with transaction.atomic():
        competition, created = QuizCompetition.objects.get_or_create(
            title="Sishemo Graduation Quiz",
            defaults={'status': 'draft'}
        )

        for number, title, category in stage_categories:
            QuizStage.objects.get_or_create(
                competition=competition,
                number=number,
                defaults={
                    'title': title,
                    'category': category,
                    'status': 'pending',
                    'question_seconds': QUESTION_SECONDS,
                    'duration_seconds': QUESTIONS_PER_STAGE * QUESTION_SECONDS,
                }
            )

    return competition


def get_participant(request):
    token = request.session.get('quiz_participant_token')

    if not token:
        return None

    return QuizParticipant.objects.filter(
        token=token
    ).first()


def load_question_bank(competition):
    file_path = (
        Path(__file__).resolve().parent
        / "data"
        / "question_bank.json"
    )

    if not file_path.exists():
        raise ValueError("question_bank.json was not found.")

    try:
        with open(file_path, encoding="utf-8") as file:
            bank = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid question bank JSON: {exc}")

    if not isinstance(bank, dict):
        raise ValueError("The question bank has an invalid format.")

    stages = {
        stage.number: stage
        for stage in QuizStage.objects.filter(
            competition=competition
        )
    }

    if len(stages) != 5:
        raise ValueError("The five quiz stages have not been created.")

    if QuizAnswer.objects.filter(
        question__stage__competition=competition
    ).exists():
        raise ValueError(
            "Answers already exist. Restart the tournament before "
            "updating its questions."
        )

    questions_to_create = []
    stage_updates = []

    for number in range(1, 6):
        stage_data = bank.get(str(number))

        if not isinstance(stage_data, dict):
            raise ValueError(f"Stage {number} is missing.")

        questions = stage_data.get("questions", [])

        if len(questions) != QUESTIONS_PER_STAGE:
            raise ValueError(
                f"Stage {number} must contain exactly "
                f"{QUESTIONS_PER_STAGE} questions."
            )

        stage = stages[number]

        for index, item in enumerate(questions, start=1):

            if not isinstance(item, dict):
                raise ValueError(
                    f"Stage {number}, question {index} is invalid."
                )

            question_text = item.get("question")
            options = item.get("options", {})
            correct = item.get("correct_option")
            points = item.get("points", 10)

            if not isinstance(question_text, str) or not question_text.strip():
                raise ValueError(
                    f"Stage {number}, question {index} has no question text."
                )

            if not isinstance(options, dict) or set(options.keys()) != {
                "A", "B", "C", "D"
            }:
                raise ValueError(
                    f"Stage {number}, question {index} needs options A-D."
                )

            if not all(
                isinstance(value, str) and value.strip()
                for value in options.values()
            ):
                raise ValueError(
                    f"Stage {number}, question {index} has an empty option."
                )

            if correct not in ["A", "B", "C", "D"]:
                raise ValueError(
                    f"Stage {number}, question {index} has an invalid answer."
                )

            if not isinstance(points, int) or points < 0:
                raise ValueError(
                    f"Stage {number}, question {index} has invalid points."
                )

            questions_to_create.append(
                QuizQuestion(
                    stage=stage,
                    order=index,
                    question_text=question_text.strip(),
                    options=options,
                    correct_option=correct,
                    points=points,
                )
            )

        stage.title = stage_data.get("title", f"Stage {number}")
        stage.category = stage_data.get("category", "")
        stage.question_seconds = QUESTION_SECONDS
        stage.duration_seconds = len(questions) * QUESTION_SECONDS

        stage_updates.append(stage)

    with transaction.atomic():

        QuizQuestion.objects.filter(
            stage__competition=competition
        ).delete()

        QuizQuestion.objects.bulk_create(questions_to_create)

        for stage in stage_updates:
            stage.save(update_fields=[
                "title",
                "category",
                "duration_seconds",
                "question_seconds",
            ])

    return len(questions_to_create)


def quiz_home(request):
    competition = QuizCompetition.objects.filter(
        status__in=['ready', 'live']
    ).order_by('-created_at').first()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'Please enter your name.')
            return redirect('graduation_quiz:home')

        if not competition:
            messages.error(request, 'Registration is currently closed.')
            return redirect('graduation_quiz:home')

        participant = get_participant(request)

        if participant and participant.competition_id == competition.id:
            request.session.set_expiry(60 * 60 * 24 * 365)
            return redirect('graduation_quiz:play')

        participant = QuizParticipant.objects.create(
            competition=competition,
            name=name,
        )

        request.session['quiz_participant_token'] = str(participant.token)
        request.session.set_expiry(60 * 60 * 24 * 365)

        return redirect('graduation_quiz:play')

    participant = get_participant(request)

    if participant and competition and participant.competition_id == competition.id:
        return redirect('graduation_quiz:play')

    return render(request, 'graduation_quiz/home.html', {
        'competition': competition,
    })


def quiz_play(request):
    participant = get_participant(request)

    if not participant:
        return redirect('graduation_quiz:home')

    return render(request, 'graduation_quiz/play.html')


def complete_stage_if_due(stage):
    if not stage or stage.status != 'active' or not stage.started_at:
        return False

    now = timezone.now()

    if (now - stage.started_at).total_seconds() < stage.duration_seconds:
        return False

    with transaction.atomic():

        locked_stage = QuizStage.objects.select_for_update().get(
            pk=stage.pk
        )

        if locked_stage.status != 'active':
            return True

        if not locked_stage.started_at:
            return False

        elapsed = (now - locked_stage.started_at).total_seconds()

        if elapsed < locked_stage.duration_seconds:
            return False

        locked_stage.status = 'completed'
        locked_stage.completed_at = now

        locked_stage.save(update_fields=[
            'status',
            'completed_at',
        ])

        if locked_stage.number == 5:
            competition = QuizCompetition.objects.select_for_update().get(
                pk=locked_stage.competition_id
            )

            competition.status = 'completed'
            competition.completed_at = now
            competition.current_stage = None

            competition.save(update_fields=[
                'status',
                'completed_at',
                'current_stage',
            ])

    return True


def quiz_status(request):
    participant = get_participant(request)

    if not participant:
        return JsonResponse({'status': 'invalid'}, status=401)

    competition = QuizCompetition.objects.select_related(
        'current_stage'
    ).filter(
        pk=participant.competition_id
    ).first()

    if not competition:
        return JsonResponse({'status': 'invalid'}, status=404)

    stage = competition.current_stage

    if not stage:
        if competition.status == 'completed':
            return JsonResponse({'status': 'competition_completed'})

        return JsonResponse({'status': 'waiting'})

    if stage.status == 'completed':
        if stage.number == 5:
            return JsonResponse({'status': 'competition_completed'})

        return JsonResponse({'status': 'stage_completed'})

    if stage.status != 'active' or not stage.started_at:
        return JsonResponse({'status': 'waiting'})

    now = timezone.now()
    elapsed = (now - stage.started_at).total_seconds()

    if elapsed >= stage.duration_seconds:
        complete_stage_if_due(stage)

        if stage.number == 5:
            return JsonResponse({'status': 'competition_completed'})

        return JsonResponse({'status': 'stage_completed'})

    question_number = int(elapsed // stage.question_seconds) + 1

    seconds_remaining = stage.question_seconds - int(
        elapsed % stage.question_seconds
    )

    question = QuizQuestion.objects.filter(
        stage=stage,
        order=question_number,
    ).first()

    if not question:
        return JsonResponse({'status': 'waiting'})

    answered = QuizAnswer.objects.filter(
        participant=participant,
        question=question,
    ).exists()

    return JsonResponse({
        'status': 'active',
        'stage': stage.number,
        'stage_title': stage.title,
        'question_number': question_number,
        'question_text': question.question_text,
        'options': question.options,
        'seconds_remaining': seconds_remaining,
        'stage_seconds_remaining': max(
            0,
            int(stage.duration_seconds - elapsed),
        ),
        'answered': answered,
    })


@require_POST
def submit_answer(request):
    participant = get_participant(request)

    if not participant:
        return JsonResponse({
            'error': 'Session expired. Please join again.'
        }, status=401)

    try:
        data = json.loads(request.body)
        selected_option = data.get('option', '')
    except (json.JSONDecodeError, AttributeError, TypeError):
        return JsonResponse({'error': 'Invalid answer.'}, status=400)

    if selected_option not in ['A', 'B', 'C', 'D']:
        return JsonResponse({'error': 'Invalid option.'}, status=400)

    competition = QuizCompetition.objects.select_related(
        'current_stage'
    ).filter(
        pk=participant.competition_id
    ).first()

    stage = competition.current_stage if competition else None

    if not stage or stage.status != 'active' or not stage.started_at:
        return JsonResponse({
            'error': 'There is no active question.'
        }, status=400)

    now = timezone.now()
    elapsed = (now - stage.started_at).total_seconds()

    if elapsed >= stage.duration_seconds:
        complete_stage_if_due(stage)

        return JsonResponse({
            'error': 'This stage has ended.'
        }, status=400)

    question_number = int(elapsed // stage.question_seconds) + 1

    question = QuizQuestion.objects.filter(
        stage=stage,
        order=question_number,
    ).first()

    if not question:
        return JsonResponse({
            'error': 'Question unavailable.'
        }, status=404)

    is_correct = selected_option == question.correct_option
    points = question.points if is_correct else 0

    with transaction.atomic():

        answer, created = QuizAnswer.objects.get_or_create(
            participant=participant,
            question=question,
            defaults={
                'selected_option': selected_option,
                'is_correct': is_correct,
                'points_awarded': points,
            },
        )

        if created and points:
            QuizParticipant.objects.filter(
                pk=participant.pk
            ).update(
                total_score=F('total_score') + points
            )

    return JsonResponse({
        'success': True,
        'already_answered': not created,
        'message': 'Answer submitted.',
    })


def quiz_leaderboard(request):
    competition = QuizCompetition.objects.filter(
        title='Sishemo Graduation Quiz'
    ).order_by('-created_at').first()

    if not competition:
        return JsonResponse({
            'status': 'not_started',
            'participants': [],
        })

    participants = competition.participants.order_by(
        '-total_score',
        'joined_at',
    )[:100]

    return JsonResponse({
        'status': competition.status,
        'participants': [
            {
                'name': participant.name,
                'score': participant.total_score,
            }
            for participant in participants
        ],
    })


def leaderboard_page(request):
    return render(
        request,
        'graduation_quiz/leaderboard.html',
    )


def quiz_results(request):
    competition = QuizCompetition.objects.filter(
        title='Sishemo Graduation Quiz'
    ).order_by('-created_at').first()

    if not competition:
        return render(request, 'graduation_quiz/results.html', {
            'winner': None,
            'participants': [],
            'competition': None,
        })

    participants = competition.participants.order_by(
        '-total_score',
        'joined_at',
    )

    winner = participants.first()

    return render(request, 'graduation_quiz/results.html', {
        'winner': winner,
        'participants': participants,
        'competition': competition,
    })


@staff_member_required
def quiz_control(request):
    competition = ensure_quiz_setup()

    if competition:
        active_stage = QuizStage.objects.filter(
            competition=competition,
            status='active',
        ).first()

        if active_stage and not active_stage.started_at:
            now = timezone.now()

            with transaction.atomic():

                QuizStage.objects.filter(
                    pk=active_stage.pk,
                    status='active',
                    started_at__isnull=True,
                ).update(started_at=now)

                QuizCompetition.objects.filter(
                    pk=competition.pk,
                ).update(
                    status='live',
                    current_stage_id=active_stage.pk,
                    started_at=competition.started_at or now,
                )

            competition.refresh_from_db()

    if request.method == 'POST':
        action = request.POST.get('action')

        if not competition:
            messages.error(request, 'Create the quiz first.')
            return redirect('graduation_quiz:control')

        if action == 'start':

            if competition.status == 'completed':
                messages.error(
                    request,
                    'This competition has already finished. '
                    'Restart it before running another tournament.'
                )

            elif competition.status == 'draft':

                try:
                    total = load_question_bank(competition)

                except ValueError as exc:
                    messages.error(request, str(exc))
                    return redirect('graduation_quiz:control')

                competition.status = 'ready'
                competition.save(update_fields=['status'])

                messages.success(
                    request,
                    f'Quiz started. {total} questions are ready. '
                    'Parents can now register.'
                )

            else:
                messages.info(
                    request,
                    'The quiz has already been started.'
                )

        elif action == 'activate':

            stage_id = request.POST.get('stage_id')

            with transaction.atomic():

                competition = QuizCompetition.objects.select_for_update().get(
                    pk=competition.pk
                )

                stage = get_object_or_404(
                    QuizStage.objects.select_for_update(),
                    pk=stage_id,
                    competition=competition,
                )

                now = timezone.now()

                active_stage = QuizStage.objects.select_for_update().filter(
                    competition=competition,
                    status='active',
                ).first()

                if active_stage:

                    if not active_stage.started_at:

                        active_stage.started_at = now
                        active_stage.save(update_fields=['started_at'])

                        competition.current_stage = active_stage
                        competition.status = 'live'
                        competition.started_at = (
                            competition.started_at or now
                        )

                        competition.save(update_fields=[
                            'current_stage',
                            'status',
                            'started_at',
                        ])

                        messages.success(
                            request,
                            f'Round {active_stage.number} has been started.'
                        )

                        return redirect('graduation_quiz:control')

                    elapsed = (
                        now - active_stage.started_at
                    ).total_seconds()

                    if elapsed >= active_stage.duration_seconds:

                        active_stage.status = 'completed'
                        active_stage.completed_at = now

                        active_stage.save(update_fields=[
                            'status',
                            'completed_at',
                        ])

                        if active_stage.number == 5:
                            competition.status = 'completed'
                            competition.completed_at = now
                            competition.current_stage = None

                            competition.save(update_fields=[
                                'status',
                                'completed_at',
                                'current_stage',
                            ])

                    else:
                        messages.error(
                            request,
                            'The current round is still running.'
                        )
                        return redirect('graduation_quiz:control')

                if competition.status == 'completed':
                    messages.error(
                        request,
                        'The competition has finished.'
                    )
                    return redirect('graduation_quiz:control')

                if stage.status != 'pending':
                    messages.error(
                        request,
                        'This round has already been started.'
                    )
                    return redirect('graduation_quiz:control')

                question_count = stage.questions.count()

                if question_count != QUESTIONS_PER_STAGE:
                    messages.error(
                        request,
                        f'Round {stage.number} needs exactly '
                        f'{QUESTIONS_PER_STAGE} questions.'
                    )
                    return redirect('graduation_quiz:control')

                previous_stages = QuizStage.objects.filter(
                    competition=competition,
                    number__lt=stage.number,
                )

                if previous_stages.exclude(status='completed').exists():
                    messages.error(
                        request,
                        'Please activate the rounds in order.'
                    )
                    return redirect('graduation_quiz:control')

                stage_start = timezone.now()

                stage_duration = question_count * QUESTION_SECONDS

                QuizStage.objects.filter(pk=stage.pk).update(
                    status='active',
                    started_at=stage_start,
                    duration_seconds=stage_duration,
                    question_seconds=QUESTION_SECONDS,
                )

                QuizCompetition.objects.filter(
                    pk=competition.pk
                ).update(
                    current_stage_id=stage.pk,
                    status='live',
                    started_at=competition.started_at or stage_start,
                )

                messages.success(
                    request,
                    f'Round {stage.number} is now running. '
                    f'{question_count} questions, '
                    f'{stage_duration // 60} minutes '
                    f'{stage_duration % 60} seconds.'
                )

        return redirect('graduation_quiz:control')

    stages = competition.stages.all() if competition else []

    return render(request, 'graduation_quiz/control.html', {
        'competition': competition,
        'stages': stages,
    })


@staff_member_required
@require_POST
def reset_quiz(request):

    competition = QuizCompetition.objects.filter(
        title='Sishemo Graduation Quiz'
    ).order_by('-created_at').first()

    if not competition:
        messages.error(request, 'No quiz competition was found.')
        return redirect('graduation_quiz:control')

    with transaction.atomic():

        QuizAnswer.objects.filter(
            participant__competition=competition
        ).delete()

        QuizParticipant.objects.filter(
            competition=competition
        ).delete()

        QuizStage.objects.filter(
            competition=competition
        ).update(
            status='pending',
            started_at=None,
            completed_at=None,
            question_seconds=QUESTION_SECONDS,
            duration_seconds=QUESTIONS_PER_STAGE * QUESTION_SECONDS,
        )

        QuizCompetition.objects.filter(
            pk=competition.pk
        ).update(
            current_stage=None,
            status='draft',
            started_at=None,
            completed_at=None,
        )

    messages.success(
        request,
        'Tournament restarted. Questions will be synchronised '
        'automatically when you start it again.'
    )

    return redirect('graduation_quiz:control')
