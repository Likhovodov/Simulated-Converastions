from django.shortcuts import render, redirect
from users.models import Student
from django.contrib.auth import login
from users.forms import NewStudentCreationForm
from django.contrib import messages
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def student_registration(request, uidb64):
    if request.method == "POST":
        form = NewStudentCreationForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get('email')

            # find the students account
            user = Student.objects.get(email=email, registered=False)

            # if the uid from the email matches the students uid, then edit user with input
            if uidb64 == urlsafe_base64_encode(force_bytes(user.pk)):
                user = Student.objects.get(email=email, registered=False)
                user.set_password(form.cleaned_data.get('password1'))
                user.first_name = form.cleaned_data.get('first_name')
                user.last_name = form.cleaned_data.get('last_name')
                user.registered = True
                user.save()
                login(request, user)
                return redirect('student-view')  # sends to the student view after completion
            else:
                messages.error(request, 'Please use link provided in email, and make sure to enter that email in'
                                        ' confirm email', fail_silently=False)

        return render(request, 'student_registration.html', {"form": form})
    return render(request, 'student_registration.html', {"form": NewStudentCreationForm()})
