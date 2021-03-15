from django.shortcuts import render
from users.models import SubjectLabel, Assignment, Student, Researcher, Email
from conversation_templates.models import ConversationTemplate
from django.core import serializers
from django.http import HttpResponse
from django.core.mail import send_mail
from django.views.decorators.csrf import ensure_csrf_cookie
from tzlocal import get_localzone
from django.contrib.auth.decorators import user_passes_test
from users.views.researcher_home import is_researcher
import json
import datetime


@user_passes_test(is_researcher)
@ensure_csrf_cookie
def create_assignment_view(request):
    curResearcher = request.user

    stud = Student.objects.all().filter(added_by=curResearcher).filter(is_active=True).values('email', 'first_name','last_name','is_active','registered')
    label = SubjectLabel.objects.all().filter(researcher=curResearcher)
    templates = ConversationTemplate.objects.all().filter(researcher=curResearcher).filter(archived=False)

    students = json.dumps(list(stud))
    subLabel = serializers.serialize("json",label)
    templates = serializers.serialize("json",templates)

    return render(request, 'create_assignment.html', {
        'students': students,
        'subjectLabels': subLabel,
        'templates': templates,
    })


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


def sendMail(subject, msg, recipient, email_address):
    send_mail(subject, msg, email_address, recipient, fail_silently=False)


# Determine if data is empty.
def isNull(data):
    if len(data)==0 or (len(data)==1 and data[0]==''):
        return True
    return False


def convert_boolean(value):
    if value == "true":
        return True
    return False


@user_passes_test(is_researcher)
def add_assignment(request):
    # Error signs and error messages.
    errMsg = ''
    success = 0

    # Get raw data
    data = request.POST
    name = data.get('name')
    assign_now = data.get('assign_now')
    date = data.get('date')
    researcher = request.user
    students = data.get('stuData')
    templates = data.get('tempData')
    labels = data.get('labelData')
    response_attempts = data.get('response_attempts')
    record_attempts = data.get('record_attempts')
    allow_typed_response = convert_boolean(data.get('allow_typed_response'))
    allow_self_rating = convert_boolean(data.get('allow_self_rating'))

    # Transfer string type list to list type
    students = decode(students)
    templates = decode(templates)
    labels = decode(labels)

    # Verify date
    datetime_now = datetime.datetime.now(get_localzone())
    if assign_now == 'true':
        sched_datetime = datetime_now
    else:
        sched_datetime = get_localzone().localize(datetime.datetime.strptime(date, "%m/%d/%Y %I:%M %p"))
    if sched_datetime < datetime_now:
        success = 1
        errMsg = errMsg+'Custom assignment date needs to be in the future.\n\n'
    # Determine if students, labels, and templates are empty.
    stuIsNull = isNull(students)
    labelIsNull = isNull(labels)
    tempIsNull = isNull(templates)

    # Save the data that can be directly assigned to assignment.
    assignment = Assignment()
    assignment.name = name
    assignment.date_assigned = sched_datetime
    researcher = Researcher.objects.get(email=researcher)
    assignment.researcher = researcher
    assignment.response_attempts = response_attempts
    assignment.recording_attempts = record_attempts
    assignment.allow_typed_response = allow_typed_response
    assignment.allow_self_rating = allow_self_rating
    assignment.save()

    # Assign student information to assignment,
    # and judge whether there is an error that both students and labels are empty.
    # Also check if chosen labels have any students in them
    if stuIsNull and labelIsNull:
        success = 1
        errMsg = errMsg+'Either students or labels must not be empty.\n\n'
    labelStudents = Student.objects.filter(labels__label_name__in=labels,
                                           labels__researcher=researcher,
                                           added_by=researcher)
    if stuIsNull and not labelIsNull:
        if stuIsNull and labelStudents.count() <= 0:
            success = 1
            errMsg = errMsg + 'The chosen label(s) does not contain any students.\n\n'
    if not stuIsNull:
        for stu in students:
            stuTmp = Student.objects.get(email=stu)
            assignment.students.add(stuTmp)
    if not labelIsNull:
        for students in labelStudents:
            stuTmp = Student.objects.get(email=students.email)
            assignment.students.add(stuTmp)
        # Assign label information to assignment
        for label in labels:
            labelTmp = SubjectLabel.objects.get(label_name=label, researcher=researcher)
            assignment.subject_labels.add(labelTmp)

    # Assign template information to assignment
    if tempIsNull:
        success = 1
        errMsg = errMsg+'Template must not be empty.\n\n'
    else:
        for temp in templates:
            tempTmp = ConversationTemplate.objects.get(pk=temp)
            assignment.conversation_templates.add(tempTmp)

    subject = 'Simulated Conversation Assignment Update'
    msg = 'You have a new assignment. Please check your home page.'
    recipient = [i[0] for i in assignment.students.values_list('email')]
    # when an error occurs, there is no need to add this task to the schedule.
    if success == 0:
        if assign_now == 'true':
            sendMail(subject, msg, recipient, 'simcon.dev@gmail.com')
        else:
            email = Email(subject=subject, message=msg, assignment=assignment)
            email.save()
    else:
        assignment.delete()

    return HttpResponse(json.dumps({
        'success': success,
        'msg': errMsg,
    }))
