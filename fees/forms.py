from django import forms
from students.models import Student

class UpdateBalanceForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["school_balance"]
        widgets = {
            "school_balance": forms.NumberInput(attrs={
                "class": "w-full border rounded px-3 py-2",
                "step": "0.01"
            })
        }
