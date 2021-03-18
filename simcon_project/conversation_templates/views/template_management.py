from django.views.generic import DeleteView, RedirectView, CreateView
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse
from django.core.mail import send_mail
from users.views.researcher_home import is_researcher
from conversation_templates.models import ConversationTemplate, TemplateFolder, TemplateResponse, TemplateNode, TemplateNodeChoice
from conversation_templates.forms import FolderCreationForm, FolderEditForm, AddTemplatesForm
from users.models import Researcher
from bootstrap_modal_forms.generic import BSModalUpdateView, BSModalDeleteView
from django_tables2 import TemplateColumn, tables, RequestConfig, A, SingleTableView
import re
import json


class FolderTemplateTable(tables.Table):
    """
    Table for showing the templates for a specific folder.
    The "delete" button has been replaced with a "remove button to
    remove a template from the folder.
    """
    hamburger_button = TemplateColumn(verbose_name='',
                                      template_name='template_management/buttons/template_hamburger_button.html',
                                      extra_context={"in_folder": True})
    name = tables.columns.LinkColumn('view-all-responses', args=[A('pk')])

    class Meta:
        attrs = {'class': 'table table-sm', 'id': 'template-table'}
        row_attrs = {'class': lambda record: 'archived' if record.archived else ''}
        model = ConversationTemplate
        fields = ['name', 'description', 'creation_date']


class AllTemplateTable(tables.Table):
    """
    Table for showing the templates for a specific folder.
    Only used when all templates are displayed.
    """
    hamburger_button = TemplateColumn(verbose_name='',
                                      template_name='template_management/buttons/template_hamburger_button.html')
    name = tables.columns.LinkColumn('view-all-responses', args=[A('pk')])

    class Meta:
        attrs = {'class': 'table table-sm', 'id': 'template-table'}
        row_attrs = {'class': lambda record: 'archived' if record.archived else '' }
        model = ConversationTemplate
        fields = ['name', 'description', 'creation_date']


class FolderTable(tables.Table):
    """
    Table showing all folders for the signed-in researcher
    """
    edit_button = tables.columns.TemplateColumn(template_name='template_management/buttons/edit_folder_button.html',
                                                verbose_name='')
    delete_button = tables.columns.Column(verbose_name='')
    name = tables.columns.LinkColumn('management:folder-view', args=[A('pk')])

    class Meta:
        attrs = {'class': 'table table-sm', 'id': 'folder-table'}
        model = TemplateFolder
        fields = ['name']


@user_passes_test(is_researcher)
@ensure_csrf_cookie
def main_view(request):
    """
    Main template management view.
    Main contents of the page are the tables showing all templates and folders the researcher has created.
    """
    show_archived = request.COOKIES.get('show_archived')
    if show_archived is None:
        request.COOKIES.get('show_archived', False)

    if show_archived == "True":
        templates = get_templates(request.user)
    else:
        templates = get_templates(request.user).filter(archived=False)

    context = main_view_helper(request, templates, None)
    return render(request, 'template_management/main_view.html', context)


@user_passes_test(is_researcher)
def folder_view(request, pk):
    """
    Main template management view.
    Shows the all folders, but shows only templates belonging to the selected folder
    """
    current_folder = get_object_or_404(TemplateFolder, pk=pk)

    show_archived = request.COOKIES.get('show_archived')
    if show_archived is None:
        request.COOKIES.get('show_archived', False)

    if show_archived == "True":
        templates = current_folder.templates.all()
    else:
        templates = current_folder.templates.filter(archived=False)

    context = main_view_helper(request, templates, current_folder)
    return render(request, 'template_management/main_view.html', context)


def main_view_helper(request, all_templates, current_folder):
    """
    Filter template table for search value and sets up folder table for the main view.
    What is displayed depends on if the user has selected a folder and if archived
    templates are being displayed or not.
    """
    templates = filter_templates(request, all_templates)

    if templates:

        if current_folder:
            template_table = FolderTemplateTable(templates, prefix="1-")
        else:
            template_table = AllTemplateTable(templates, prefix="1-")

        RequestConfig(request, paginate={"per_page": 10}).configure(template_table)
    else:
        template_table = None

    folders = filter_folder(request)
    if folders:
        folders = folders.order_by('name')
        folder_table = FolderTable(folders, prefix="2-")
        RequestConfig(request, paginate={"per_page": 10}).configure(folder_table)
    else:
        folder_table = None

    template_list = None
    if current_folder:
        template_list = ConversationTemplate.objects.filter(researcher=request.user.id, archived=False)
        for template in current_folder.templates.all():
            template_list = template_list.exclude(id=template.id)

    context = {
        'templateTable': template_table,
        'folderTable': folder_table,
        'current_folder': current_folder,
        'show_archived': request.COOKIES.get('show_archived'),
        'all_folders': TemplateFolder.objects.filter(researcher=request.user.id),
        'templates': templates.order_by('name'),
        'folder_creation_form': FolderCreationForm(request=request.user.id),
        'add_templates_form': AddTemplatesForm(),
        'all_templates': template_list,
    }

    return context


class FolderTableView(SingleTableView):
    model = TemplateFolder
    table_class = FolderTable
    template_name = "template_management/folder_table.html"


def create_folder(request):
    if request.POST.get('folder_name'):
        new_folder = FolderCreationForm(request.POST, request=request)
        if new_folder.is_valid():
            folder_name = new_folder.cleaned_data.get('folder_name')
            researcher = Researcher.objects.get(id=request.user.id)
            TemplateFolder().create_folder(folder_name, researcher)

    back = request.POST.get('back', '/')
    return redirect(back)


def add_templates(request, pk):
    folder = get_object_or_404(TemplateFolder, pk=pk)
    if request.POST.get('templates'):
        form = AddTemplatesForm(request.POST)
        if form.is_valid():
            for template in request.POST.getlist('templates'):
                folder.templates.add(template)

    back = request.POST.get('back', '/')
    return redirect(back)


class RedirectToTemplateCreation(RedirectView):
    url = reverse_lazy('management:create-conversation-template-view')


class FolderEditView(BSModalUpdateView):
    """
    A modal that appears on top of the main_view to edit the contents of a folder
    """
    model = TemplateFolder
    template_name = 'template_management/edit_folder_name_modal.html'
    form_class = FolderEditForm

    def get_success_url(self):
        success_url = route_to_current_folder(self.request.META.get('HTTP_REFERER'))
        return success_url


@user_passes_test(is_researcher)
def share_template_modal(request, pk):
    """
    A modal to share a template with other researchers
    """
    template = ConversationTemplate.objects.filter(pk=pk).first()
    return render(request,
                  'template_management/share_template_modal.html',
                  {'template_name': template.name,
                   'template_pk': pk})


@user_passes_test(is_researcher)
@ensure_csrf_cookie
def validate_share_email(request):
    """
    Confirm that entered in email is in database and user isn't sharing with themselves.
    """
    success = 0
    name = ''
    email_address = request.POST.get("email")
    researcher = Researcher.objects.filter(email=email_address).first()
    if researcher is None:
        success = 1
    elif researcher == Researcher.objects.filter(id=request.user.id).first():
        success = 2
    else:
        name = researcher.first_name + ' ' + researcher.last_name

    return HttpResponse(json.dumps({
        'success': success,
        'name': name,
    }))


@user_passes_test(is_researcher)
@ensure_csrf_cookie
def share_template_finalize(request):
    """
    Clone template and share with each researcher specified in modal.
    """
    success = 0
    error_message = ''
    template_pk = request.POST.get("pk")
    template = ConversationTemplate.objects.filter(pk=template_pk).first()
    researchers = decode(request.POST.get("researchers"))
    if template is None:
        success = 1
        error_message += 'Invalid template selection.\n'
    if researchers is None or researchers == '':
        success = 1
        error_message += 'No researchers selected.\n'
    # for each researcher, clone template, all it's nodes and each node's choices.
    if success == 0:
        for researcher_email in researchers:
            template_clone = template
            nodes = TemplateNode.objects.filter(parent_template=template)
            template_clone.pk = None
            template_clone.researcher = Researcher.objects.filter(email=researcher_email).first()
            template_clone.save()
            for node in nodes:
                node_clone = node
                node_choices = TemplateNodeChoice.objects.filter(parent_template_node=node)
                node_clone.pk = None
                node_clone.parent_template = template_clone
                node_clone.save()
                for node_choice in node_choices:
                    choice_clone = node_choice
                    choice_clone.pk = None
                    choice_clone.parent_template_node = node
                    choice_clone.save()

    sender = Researcher.objects.filter(id=request.user.id)
    sender_name = str(sender.first().get_full_name())
    sender_email = str(sender.first())
    template_name = str(template)
    subject = 'Simulated Conversations Template Shared with You'
    msg = sender_name + ' (' + sender_email + ') ' + 'has shared \"' + template_name + '\" with you on Simulated ' \
                                                                                       'Conversations.'
    send_mail(subject, msg, 'simcon.dev@gmail.com', researchers, fail_silently=False)
    return HttpResponse(json.dumps({
        'success': success,
        'message': error_message,
    }))


# Transfer string type list to list type
def decode(str):
    if str[0] != '[':
        return
    temp = str[1:-1]
    temp = temp.split(',')
    listTmp = []
    for t in temp:
        t = t[1:-1]
        listTmp.append(t)
    return listTmp


class FolderDeleteView(DeleteView):
    """
    Deletes a folder. Routes to the main_view (all templates showing)
    if the current folder that is being viewed is deleted.
    """
    model = TemplateFolder
    success_url = reverse_lazy('management:main')


class TemplateDeleteView(BSModalDeleteView):
    """
    Deletes a template. Confirmation modal pops up to make sure
    the user wants to delete a template.
    """
    model = ConversationTemplate
    template_name = 'template_management/template_delete_modal.html'
    success_message = None  # Don't delete this. BSModalDeleteView needs success message for some reason
    success_url = reverse_lazy('management:main')

    def get(self, request, *args, **kwargs):
        """
        Override post to send template name and name of assignment that
        will be removed as context to the template
        """
        super().get(request, *args, **kwargs)
        this_template = ConversationTemplate.objects.get(pk=self.kwargs['pk'])
        assignments = this_template.assignments.all()
        to_delete = []
        for assignment in assignments:
            if assignment.conversation_templates.all().count() == 1:
                to_delete.append(assignment.name)
        context = {"template_name": this_template.name, "assignments": to_delete}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Override post to remove assignment if the template being deleted
        is the only one in the assignment.
        """
        this_template = ConversationTemplate.objects.get(pk=self.kwargs['pk'])
        assignments = this_template.assignments.all()
        for assignment in assignments:
            if assignment.conversation_templates.all().count() == 1:
                assignment.delete()
        super().post(request, *args, **kwargs)
        return redirect(reverse('management:main'))


def remove_template(request, pk):
    """
    Remove the chosen template from the current folder in view.
    This does not delete the template.
    """
    if request.method == 'POST':
        previous_url = request.META.get('HTTP_REFERER')
        folder_pk = re.findall(r"/folder/([A-Za-z0-9\-]+)", previous_url)[0]
        template = get_object_or_404(ConversationTemplate, pk=pk)
        folder = get_object_or_404(TemplateFolder, pk=folder_pk)
        folder.templates.remove(template)
        back = request.POST.get('back', '/')
        return redirect(back)


def update_cookie(request, show_archived):
    back = request.POST.get('back', '/')
    response = redirect(back)

    if int(show_archived) == 0:
        response.set_cookie('show_archived', False)
    else:
        response.set_cookie('show_archived', True)

    return response


def archive_template(request, pk):
    template = get_object_or_404(ConversationTemplate, pk=pk)
    if template.archived:
        ConversationTemplate.objects.filter(pk=pk).update(archived=False)
        TemplateResponse.objects.filter(template=template.id).update(archived=False)
    else:
        ConversationTemplate.objects.filter(pk=pk).update(archived=True)
        TemplateResponse.objects.filter(template=template.id).update(archived=True)

    back = request.POST.get('back', '/')
    return redirect(back)


def route_to_current_folder(previous_url):
    """
    If a folder is being viewed returns to the folder view, else to main view
    Used to reroute generic editing views
    """
    if "folder" in previous_url:
        folder_id = re.findall(r"/folder/([A-Za-z0-9\-]+)", previous_url)[0]
        return reverse_lazy('management:folder-view', args=[folder_id])
    else:
        return reverse_lazy('management:main')


def filter_folder(request):
    folder_filter = request.GET.get('folder-filter')
    if folder_filter is not None:
        return TemplateFolder.objects.filter(researcher=request.user.id, name__contains=folder_filter)
    return TemplateFolder.objects.filter(researcher=request.user.id)


def filter_templates(request, templates):
    template_filter = request.GET.get('template-filter')
    if template_filter is not None:
        # Constraint to filter for names OR descriptions that contain the search value
        filter_fields = Q(name__contains=template_filter) | Q(description__contains=template_filter)
        return templates.filter(filter_fields)
    return templates


def get_templates(user):
    researcher = get_object_or_404(Researcher, email=user)
    return ConversationTemplate.objects.filter(researcher=researcher)
