from django import forms
from .models import ImportSession


class ImportSessionForm(forms.ModelForm):

    class Meta:
        model = ImportSession
        fields = [
            "grade",
            "subject",
            "topic",
            "title",
            "source_file",
            "start_page",
            "end_page",
        ]

        widgets = {
            "grade": forms.Select(attrs={
                "class": "w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-gray-700 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-none transition",
            }),

            "subject": forms.Select(attrs={
                "class": "w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-gray-700 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-none transition",
            }),

            "topic": forms.Select(attrs={
                "class": "w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-gray-700 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-none transition",
            }),

            "title": forms.TextInput(attrs={
                "class": "w-full rounded-xl border border-gray-300 px-4 py-3 text-gray-700 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-none transition",
                "placeholder": "e.g. Introduction to Computers",
            }),

            "source_file": forms.ClearableFileInput(attrs={
                "class": (
                    "block w-full text-sm text-gray-700 "
                    "border border-gray-300 rounded-xl cursor-pointer "
                    "bg-gray-50 file:mr-4 file:rounded-lg file:border-0 "
                    "file:bg-indigo-600 file:px-4 file:py-2 "
                    "file:text-white hover:file:bg-indigo-700"
                ),
                "accept": ".pdf",
            }),

            "start_page": forms.NumberInput(attrs={
                "class": "w-full rounded-xl border border-gray-300 px-4 py-3 text-gray-700 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-none transition",
                "min": 1,
                "placeholder": "Start page",
            }),

            "end_page": forms.NumberInput(attrs={
                "class": "w-full rounded-xl border border-gray-300 px-4 py-3 text-gray-700 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-none transition",
                "min": 1,
                "placeholder": "End page",
            }),
        }