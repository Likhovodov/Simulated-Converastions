from users.forms import NewLabel, AddToLabel
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.http import urlsafe_base64_encode
from users.models import Student, Researcher, SubjectLabel, Assignment
from conversation_templates.models import TemplateResponse
from django.core.mail import send_mail
import django_tables2 as tables
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from users.views.researcher_home import is_researcher
from django.views.decorators.csrf import ensure_csrf_cookie
from django_tables2 import RequestConfig
import json


class AllStudentList(tables.Table):  # collects info from students to display on the table
    delete = tables.TemplateColumn(template_name='delete_student_button.html', verbose_name='')
    remove = tables.TemplateColumn(template_name='remove_student_button.html', verbose_name='')

    class Meta:
        attrs = {'class': 'table table-sm', 'id': 'student-table'}
        model = Student
        fields = ['email', 'first_name', 'last_name', 'registered']


class LabelList(tables.Table):  # collects the table names
    label_name = tables.Column(linkify={"viewname": "student-management", "args": [tables.A("label_name")]},
                               accessor='label_name', verbose_name='Label Name')
    delete = tables.TemplateColumn(template_name='delete_label_button.html', verbose_name='')

    class Meta:
        attrs = {'class': 'table table-sm', 'id': 'label-table'}
        model = SubjectLabel
        fields = ['label_name']


@user_passes_test(is_researcher)
def student_management(request, name="All Students"):
    # gets current researcher for use later
    researcher = Researcher.objects.filter(email=request.user).first()

    # if the label with label_name = name is not found load default of All Students
    if not SubjectLabel.objects.filter(label_name=name, researcher=researcher):
        name = "All Students"

    # if researcher presses a submit button
    if request.method == "POST":
        if request.POST.get('Students'):
            label = SubjectLabel.objects.get(label_name=name, researcher=researcher)
            students = Student.objects.filter(id__in=request.POST.getlist('Students'))
            for student in students:
                label.students.add(student)
            if students.count() != len(request.POST.getlist('Students')):
                messages.error(request, 'Invalid input', fail_silently=False)

        if request.POST.get('label_name'):  # create new label
            save_folder = NewLabel(request.POST)
            if save_folder.is_valid():
                label_name = save_folder.cleaned_data.get("label_name")

                # if the label does not already exist, create it
                if not SubjectLabel.objects.filter(label_name=label_name, researcher=researcher):
                    SubjectLabel().create_label(label_name, researcher)
                else:
                    messages.error(request, 'Label name already exists',
                                   fail_silently=False)

    # creates the table for the labels
    all_lbl = SubjectLabel.objects.filter(researcher=researcher)
    label_table = LabelList(all_lbl, prefix="1-")
    RequestConfig(request, paginate={"per_page": 10}).configure(label_table)

    # creates the table for the students in current label
    stu_contents = SubjectLabel.objects.get(label_name=name, researcher=researcher).students.all()
    student_table = AllStudentList(stu_contents, prefix="2-")
    if name == "All Students":
        student_table.exclude = ('remove',)
    RequestConfig(request, paginate={"per_page": 10}).configure(student_table)

    add_students = Student.objects.filter(added_by=researcher)

    return render(request, 'student_management.html',  {"name": name, "form": AddToLabel(), "form2": NewLabel(),
                                                         'stu_table': student_table,
                                                        'lbl_table': label_table, 'add_students': add_students})


def student_remove_view(request, pk):
    if request.POST:
        researcher = request.user.id
        back = request.POST.get('back')
        back_len = len(back)
        name = back[21:back_len-1]
        label = SubjectLabel.objects.get(label_name=name, researcher=researcher).students
        student = Student.objects.get(id=pk)
        label.remove(student)
        return redirect(back)


def delete_label_view(request, pk):
    if request.POST:
        back = request.POST.get('back')
        label = SubjectLabel.objects.get(id=pk)
        label.delete()
        return redirect(back)


@user_passes_test(is_researcher)
def create_students_modal(request):
    """
    A modal that appears on top of the main_view to create a student
    """
    return render(request, 'student_creation_modal.html')


@user_passes_test(is_researcher)
@ensure_csrf_cookie
def validate_student_email(request):
    """
    Confirm email does not belong to researcher account and that email doesn't belong to a registered student who
    the researcher has added before
    """
    success = 0
    email_address = request.POST.get("email")
    researcher = Researcher.objects.filter(email=email_address).first()
    student = Student.objects.filter(email=email_address, added_by=request.user).first()
    if researcher is not None:
        success = 1
    if student is not None and student.registered is True:
        success = 2

    return HttpResponse(json.dumps({
        'success': success,
    }))


@user_passes_test(is_researcher)
@ensure_csrf_cookie
def register_students(request):
    """
    Send registration emails to newly made accounts and attach all students to researcher
    """
    success = 0
    error_message = ''
    students = decode(request.POST.get("students"))
    if students is None or students == '':
        success = 1
        error_message += 'No emails entered.\n'
    # for each student, check if account already exists. If no, send registration email. Add researcher to added_by list
    if success == 0:
        subject = 'Activate Your Simulated Conversations account'
        current_site = get_current_site(request)
        site = current_site.domain
        message = 'Hi, \nPlease register here: \nhttp://' + site + '/student/register/'
        for student_email in students:
            student = Student.objects.filter(email=student_email).first()
            if student is None:
                student = Student.objects.create(email=student_email, first_name='N/A', last_name='N/A',
                                                 is_researcher=False)
            if student.registered is False:
                student.set_unusable_password()
                uid = urlsafe_base64_encode(force_bytes(student.pk))
                message = message + uid + '\n'
                send_mail(subject, message, 'simcon.dev@gmail.com', [student_email], fail_silently=False)
            student.added_by.add(request.user.id)
            all_students_label = SubjectLabel.objects.filter(label_name='All Students',
                                                             researcher=request.user.id).first()
            all_students_label.students.add(student)
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


def delete_students_modal(request, pk):
    """
    Confirmation modal to confirm researcher wants to remove them. If student has only been added by one researcher,
    the student is deleted. Otherwise, the researcher is removed from the added_by list and the student's
    responses to that researcher's templates are deleted.
    """
    if request.POST:
        student = Student.objects.filter(pk=pk).first()
        if student is not None:
            added_by_count = Student.objects.filter(email=student).first().added_by.count()
            if added_by_count > 1:
                student.added_by.remove(request.user.id)
                for label in SubjectLabel.objects.filter(researcher=request.user.id):
                    label.students.remove(student)
                for assignment in Assignment.objects.filter(researcher=request.user.id, students=student):
                    assignment.students.remove(student)
                TemplateResponse.objects.filter(student=student, template__researcher=request.user).delete()
            else:
                student.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return render(request, 'student_delete_modal.html')
