from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Student, SubjectLabel, Researcher
import django_tables2 as tables
from django.forms import ModelForm


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = CustomUser
        fields = ('email',)


class NewStudentCreationForm(forms.Form):
    email = forms.EmailField(max_length=254, required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    password1 = forms.CharField(max_length=100, required=True, widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=100, required=True, widget=forms.PasswordInput)


class StudentTable(tables.Table):
    class Meta:
        model = Student


class PassReset(forms.Form):
    email = forms.EmailField(max_length=254, required=True)


class LabelTable(tables.Table):
    class Meta:
        model = SubjectLabel


class AddToLabel(forms.Form):
    email = forms.EmailField(max_length=254, required=True, widget=forms.TextInput(attrs={'placeholder': 'Student name'}), label='')


class SendEmail(forms.Form):
    student_email = forms.EmailField(max_length=254, required=True)


class NewLabel(forms.Form):
    label_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Label name'}), label='')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email',)


class UpdateTranscription(forms.Form):
    transcription = forms.CharField(help_text="Enter new transcription")


class NewResearcherCreationForm(forms.Form):
    email = forms.EmailField(max_length=254, required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    password1 = forms.CharField(max_length=100, required=True, widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=100, required=True, widget=forms.PasswordInput)


class AddResearcherForm(ModelForm):
    class Meta:
        model = Researcher
        fields = ('email',)
