from django.db import models
from Core.models import Section, Grade, Subject, Topic


class ImportSession(models.Model):
    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        PREVIEW = "preview", "Preview"
        COMPLETED = "completed", "Completed"

    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)

    source_file = models.FileField(upload_to="imports/")

    start_page = models.PositiveIntegerField()
    end_page = models.PositiveIntegerField()

    generated_html = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title