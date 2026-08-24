from django import forms
from .models import Test, StudentScore, Subject




# Formset for entering student scores
class StudentScoreForm(forms.ModelForm):
    class Meta:
        model = StudentScore
        fields = ["student", "score"]
        widgets = {
            "student": forms.HiddenInput()
        }
