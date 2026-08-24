from django import forms
from django.contrib.auth.models import User
from .models import Student
from accounts.models import UserProfile

class StudentCreateForm(forms.ModelForm):
    # Fields for User
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Student
        fields = [
            'photo', 'full_photo', 'parent',
            'on_transport', 'on_school_lunch',
            'height_cm', 'nationality', 'tribe', 'address'
        ]

    def save(self, commit=True, grade=None):
        # 1. Create the User
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password']
        )

        # 2. Create the UserProfile
        profile = UserProfile.objects.create(
            user=user,
            role='student'
        )

        # 3. Create the Student
        student = super().save(commit=False)
        student.profile = profile
        if grade:
            student.grade = grade
        if commit:
            student.save()
        return student
