from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Student, SubjectLabel, Researcher
import django_tables2 as tables
from django.forms import ModelForm
from django_select2 import forms as s2forms
from django.core.exceptions import ValidationError


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

    def clean(self):
        data = self.cleaned_data
        password1 = data["password1"]
        password2 = data["password2"]
        email = data["email"]

        if password1 != password2:
            self.add_error('password2', 'Passwords do not match')
        if not Student.objects.filter(email=email, registered=False):
            if Student.objects.filter(email=email, registered=True):
                self.add_error('email', 'Account already created')
            else:
                self.add_error('email', 'Invalid email address, please enter the email address that'
                                        ' you received the email at.')
        return data


class StudentTable(tables.Table):
    class Meta:
        model = Student


class StudentWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "name__icontains",
    ]


class AddStudentForm(forms.ModelForm):
    class Meta:
        model = SubjectLabel
        fields = ['students']
        widgets = {
            "students": StudentWidget,
        }


class PassReset(forms.Form):
    email = forms.EmailField(max_length=254, required=True)


class LabelTable(tables.Table):
    class Meta:
        model = SubjectLabel


class AddToLabel(forms.Form):
    email = forms.EmailField(max_length=254, required=True, widget=forms.TextInput(attrs={'placeholder': 'Student email'}), label='')


class SendEmail(forms.Form):
    student_email = forms.EmailField(max_length=254, required=True, widget=forms.TextInput(attrs={'placeholder': 'Student email'}), label='')


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
        fields = ['email']
