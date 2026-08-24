from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import Event


# All Events
def events_list(request):
    events = Event.objects.all()

    return render(request, 'events/events_list.html', {
        'events': events
    })


# Single Event
def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug)

    return render(request, 'events/event_detail.html', {
        'event': event
    })