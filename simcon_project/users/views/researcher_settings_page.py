from django.contrib.auth.decorators import user_passes_test
from users.views.researcher_home import is_researcher
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render


@user_passes_test(is_researcher)
def researcher_settings_view(request):

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'researcher_settings_view.html', {'form': form})
