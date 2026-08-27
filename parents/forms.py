from django import forms
from django.contrib.auth.models import User
from accounts.models import UserProfile
from students.models import Student
from .models import Parent
from django.db import transaction


class ParentCreateForm(forms.ModelForm):
    # User fields
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    # Select children
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Parent
        fields = []  # Add Parent-specific fields if needed

    # ✅ Field validation
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "This username is already taken. Please choose another one."
            )
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email is already registered. Please use a different one."
            )
        return email

    # ✅ Save everything inside a transaction
    def save(self, commit=True):
        with transaction.atomic():
            # 1. Create User
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password']
            )

            # 2. Create Profile
            profile = UserProfile.objects.create(
                user=user,
                role='parent'
            )

            # 3. Create Parent
            parent = Parent.objects.create(profile=profile)

            # 4. Assign Children
            selected_students = self.cleaned_data.get("students")
            if selected_students:
                parent.children.set(selected_students)

            return parent
