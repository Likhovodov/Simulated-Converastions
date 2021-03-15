from django.shortcuts import render, redirect
from users.models import Researcher
from django.contrib.auth import login
from users.forms import NewResearcherCreationForm
from django.contrib import messages
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def researcher_registration(request, uidb64):
    """
    This displays a form for the researcher to confirm their account details entered in by the admin
    and to set their password. Sends user to the researcher home page.
    """
    if request.method == "POST":
        form = NewResearcherCreationForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get('email')

            # find the students account
            user = Researcher.objects.get(email=email, registered=False)

            # if the uid from the email matches the students uid, then edit user with input
            if uidb64 == urlsafe_base64_encode(force_bytes(user.pk)):
                user = Researcher.objects.get(email=email, registered=False)
                user.set_password(form.cleaned_data.get('password1'))
                user.first_name = form.cleaned_data.get('first_name')
                user.last_name = form.cleaned_data.get('last_name')
                user.registered = True
                user.save()
                login(request, user)
                return redirect('researcher-view')  # sends to the student view after completion
            else:
                messages.error(request, 'Please use link provided in email, and make sure to enter that email in'
                                        ' confirm email', fail_silently=False)

        return render(request, 'researcher_registration.html', {"form": form})
    return render(request, 'researcher_registration.html', {"form": NewResearcherCreationForm()})
