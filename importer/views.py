from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from Core.models import Note
from .forms import ImportSessionForm
from .models import ImportSession
from .services.ai_service import AIService
from .services.pdf_service import PDFService


def import_note(request):
    """
    Upload PDF -> Extract -> AI -> Save ImportSession -> Preview
    """

    if request.method == "GET":
        form = ImportSessionForm()
        return render(
            request,
            "importer/import_form.html",
            {"form": form},
        )

    form = ImportSessionForm(request.POST, request.FILES)

    if not form.is_valid():
        return render(
            request,
            "importer/import_form.html",
            {"form": form},
        )

    grade = form.cleaned_data["grade"]
    subject = form.cleaned_data["subject"]
    topic = form.cleaned_data["topic"]
    title = form.cleaned_data["title"]

    uploaded_pdf = form.cleaned_data["source_file"]

    start_page = form.cleaned_data["start_page"]
    end_page = form.cleaned_data["end_page"]

    # ---------------------------------------------
    # Save Import Session
    # ---------------------------------------------

    session = form.save(commit=False)

    # Automatically determine section from grade
    session.section = grade.section

    session.status = ImportSession.Status.PROCESSING

    session.save()

    # ---------------------------------------------
    # Extract PDF
    # ---------------------------------------------

    pdf = PDFService(uploaded_pdf)

    extracted = pdf.extract(
        start_page=start_page,
        end_page=end_page,
        image_output_dir=Path(settings.MEDIA_ROOT) / "imports",
    )

    # ---------------------------------------------
    # Generate AI Notes
    # ---------------------------------------------

    ai = AIService()

    generated_html = ai.generate_notes(
        grade=grade.name,
        subject=subject.name,
        topic=topic.title,
        title=title,
        extracted_text=extracted.text,
    )

    # ---------------------------------------------
    # Save AI Result
    # ---------------------------------------------

    session.generated_html = generated_html
    session.status = ImportSession.Status.PREVIEW
    session.save(update_fields=["generated_html", "status"])

    return render(
        request,
        "importer/preview.html",
        {
            "session": session,
            "grade": grade,
            "subject": subject,
            "topic": topic,
            "title": title,
            "generated_html": generated_html,
            "images": extracted.images,
            "start_page": start_page,
            "end_page": end_page,
        },
    )


def save_note(request):
    """
    Save generated notes into the Notes table.
    """

    if request.method != "POST":
        return redirect("import_note")

    session = get_object_or_404(
        ImportSession,
        pk=request.POST.get("session_id"),
    )

    note = Note.objects.create(
        topic=session.topic,
        title=session.title,
        content=session.generated_html,
    )

    session.status = ImportSession.Status.COMPLETED
    session.save(update_fields=["status"])

    messages.success(
        request,
        "Notes imported successfully.",
    )

    return redirect("import_note")