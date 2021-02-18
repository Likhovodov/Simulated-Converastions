from django.contrib.auth.decorators import user_passes_test
from users.views.researcher_home import is_researcher
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse_lazy
import django_tables2 as tables
from users.forms import AddResearcherForm
from users.models import Researcher
from bootstrap_modal_forms.generic import BSModalDeleteView


class ResearcherTable(tables.Table):
    """
    Table of researchers showing their names and emails.
    first_name is the first name of the researcher.
    last_name is the last name of the researcher.
    email_address is the email address of the researcher used for account creation.
    delete is a button to display a modal to delete the researcher from the database
    """
    first_name = tables.Column(accessor='first_name')
    last_name = tables.Column(accessor='last_name')
    email_address = tables.Column(accessor='email')
    delete = tables.TemplateColumn(verbose_name='', template_name='settings/delete_researcher_button.html')


class ResearcherDeleteView(BSModalDeleteView):
    """
    Deletes a researcher. Confirmation modal pops up to make sure
    the user wants to delete the researcher.
    """
    model = Researcher
    template_name = 'settings/researcher_delete_modal.html'
    success_message = 'Success: Researcher was deleted.'
    success_url = reverse_lazy('settings:main')

    def get(self, request, *args, **kwargs):
        """
        Override post to send email address of researcher that
        will be removed as context to the template
        """
        super().get(request, *args, **kwargs)
        researcher = Researcher.objects.get(pk=self.kwargs['pk'])
        context = {"researcher": researcher}
        return render(request, self.template_name, context)


@user_passes_test(is_researcher)
def researcher_settings_view(request):
    """
    This determines if the user is an admin (staff) or not then displays the appropriate view.
    :param request: HttpRequest used to determine what type of user is accessing view (admin/staff or not)
    :return: the HttpRequest object that is returned by the Admin or Standard Settings Views.
    """
    user = get_user_model()
    # determine if user an admin (is_staff) and fetch forms/table accordingly
    if user.get_is_staff(request.user):
        change_password_form = change_password(request)
        add_researcher_form = add_researcher(request)
        researchers_table = get_current_researchers(request)
    else:
        change_password_form = change_password(request)
        add_researcher_form = None
        researchers_table = None
    return render(request, 'researcher_settings_view.html', {
        'change_password_form': change_password_form,
        'add_researcher_form': add_researcher_form,
        'researchers_table': researchers_table,
    })


@user_passes_test(is_researcher)
def change_password(request):
    """
    Displays and validates Django default PasswordChangeForm
    :param request:
    :return:
    """
    if request.method == 'POST':
        change_password_form = PasswordChangeForm(request.user, request.POST)
        if change_password_form.is_valid():
            user = change_password_form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return PasswordChangeForm(request.user)
        else:
            if 'change_password' in request.POST:
                messages.error(request, 'Please make sure you\'ve typed in everything correctly and try again.')
            return PasswordChangeForm(request.user)
    else:
        return PasswordChangeForm(request.user)


@user_passes_test(is_researcher)
def get_current_researchers(request):
    """
    Queries database for all researchers and creates django_table showing their names and emails.
    :param request:
    :return:
    """
    researchers = Researcher.objects.exclude(id=request.user.id)
    if researchers.count() > 0:
        researchers_table = ResearcherTable(researchers)
        researchers_table.paginate(page=request.GET.get("page", 1), per_page=10)
        return researchers_table
    else:
        return None


@user_passes_test(is_researcher)
def add_researcher(request):
    """
    Creates and validates the AddResearcherForm. If AddResearcherForm is valid, an account registration email is
        generated and sent to the email address specified in the form. That email will contain a link
        for the user to register their account.
        First and last names for brand new researchers will both be "N/A". These are overwritten once the researcher
        has completed account creation by following the link sent to them.
    :param request:
    :return: the form to add new researchers.
    """
    if request.method == 'POST':
        add_researcher_form = AddResearcherForm(request.POST)
        if add_researcher_form.is_valid():
            email_address = add_researcher_form.cleaned_data.get('email')
            user = Researcher.objects.create(email=email_address, first_name='N/A', last_name='N/A',
                                             is_researcher=True)
            user.set_unusable_password()
            current_site = get_current_site(request)
            subject = 'Activate Your Simulated Conversations account'
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            site = current_site.domain
            message = 'Hi, \nPlease register here: \nhttp://' + site + '/researcher/register/' \
                      + uid + '\n'
            send_mail(subject, message, 'simulated.conversation@mail.com', [email_address], fail_silently=False)
            messages.success(request, 'A link to register has been sent to the researcher\'s email provided.')
            return AddResearcherForm()
        else:
            if 'add_researcher' in request.POST:
                messages.error(request, 'Please check the researcher information you typed in and try again.')
            return AddResearcherForm()
    else:
        return AddResearcherForm()
