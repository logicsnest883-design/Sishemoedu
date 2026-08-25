from django import forms
from .models import Test, StudentScore




# Formset for entering student scores
class StudentScoreForm(forms.ModelForm):
    class Meta:
        model = StudentScore
        fields = ["student", "score"]
        widgets = {
            "student": forms.HiddenInput()
        }
