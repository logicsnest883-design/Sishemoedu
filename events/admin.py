from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Event, Activity, ActivityImage


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_date', 'location']
    prepopulated_fields = {'slug': ('title',)}



@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "location", "featured", "published")
    list_filter = ("featured", "published")
    search_fields = ("title", "short_description", "description")


@admin.register(ActivityImage)
class ActivityImageAdmin(admin.ModelAdmin):
    list_display = ("activity", "caption", "order")
    list_filter = ("activity",)
    search_fields = ("activity__title", "caption")
    ordering = ("activity", "order", "id")