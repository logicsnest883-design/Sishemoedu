from django.db import models
from ckeditor.fields import RichTextField

# Create your models here.
from django.db import models
from django.utils.text import slugify


class Section(models.Model):
    SECTION_CHOICES = [
        ('lower', 'Lower Primary'),
        ('upper', 'Upper Primary'),
        ('secondary', 'Secondary'),
    ]
    name = models.CharField(max_length=20, choices=SECTION_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()




class Grade(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='grades')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


from django.utils.text import slugify

class Book(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="books")
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to="books/")  # PDF, DOCX, etc.
    
    # Optional fields for in-site display
    cover_image = models.ImageField(upload_to="book_covers/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)  # for nice URLs


    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # auto-generate slug from title if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)



class Subject(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("section", "name")

    def __str__(self):
        return f"{self.name} ({self.section})"

class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, null=True, blank=True)

    title = models.CharField(max_length=200)
    order = models.IntegerField(default=0)


    class Meta:
        unique_together = ("subject", "grade", "title")

    def __str__(self):
        grade_name = self.grade.name if self.grade else "No Grade"
        return f"{self.title} - {self.subject.name} - {grade_name}"





class Note(models.Model):
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="notes"
    )

    title = models.CharField(max_length=200)

    # Text content
    content = RichTextField(blank=True, null=True)

    # PDF or document upload
    document = models.FileField(
        upload_to="notes/documents/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError

        # Require either text content or a document
        if not self.content and not self.document:
            raise ValidationError(
                "Provide either note content or upload a document."
            )


from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify

class Comprehension(models.Model):
    grade = models.ForeignKey("Grade", on_delete=models.CASCADE, related_name="comprehensions")
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="comprehension_images/", blank=True, null=True)

    # NEW: Story content using CKEditor
    story = RichTextField(null=True, blank=True)

    # Optional: questions (you can remove if you want story only)
    questions = RichTextField(blank=True, null=True)

    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


