from django.db import models
from django.utils.text import slugify





class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    image = models.ImageField(upload_to='events/', blank=True, null=True)

    description = models.TextField()

    location = models.CharField(max_length=255)

    start_date = models.DateField()
    end_date = models.DateField()

    start_time = models.TimeField()
    end_time = models.TimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']


    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)




class Activity(models.Model):
    title = models.CharField(max_length=200)
    short_description = models.TextField()
    description = models.TextField()
    cover_image = models.ImageField(upload_to="activities/covers/")
    date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    featured = models.BooleanField(default=False)
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return self.title


class ActivityImage(models.Model):
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="activities/gallery/")
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.activity.title} - Image"