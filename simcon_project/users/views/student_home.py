from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Max, Min
from users.models import *
from conversation_templates.models import *
import django_tables2 as tables
from django_tables2 import RequestConfig
import datetime
from tzlocal import get_localzone


def is_student(user):
    return user.is_authenticated and not user.get_is_researcher()


class IncompleteTemplatesTable(tables.Table):
    """
    Table of assigned conversation templates with no responses for a given student.
    name is the name of the template assigned. links to conversation-start
    date_assigned is the date that template was assigned.
    completion_date is the date the template was last completed by the student or is null.
    """
    name = tables.Column(linkify=("conversation-start",
                                  {"ct_id": tables.A("conversation_templates__id"),
                                   "assign_id": tables.A("id")
                                   }),
                         accessor='conversation_templates__name',
                         verbose_name='Template Name')
    date_assigned = tables.Column(verbose_name='Date Assigned')


class CompletedTemplatesTable(tables.Table):
    """
    Table of assigned conversation templates with at least one responses for a given student.
    name is the name of the template assigned. links to conversation-start
    date_assigned is the date that template was assigned.
    completion_date is the date the template was last completed by the student or is null.
    """
    name = tables.Column(linkify=("conversation-start",
                                  {"ct_id": tables.A("conversation_templates__id"),
                                   "assign_id": tables.A("id")
                                   }),
                         accessor='conversation_templates__name',
                         verbose_name='Template Name')
    date_assigned = tables.Column(verbose_name='Date Assigned')
    completion_date = tables.Column(accessor='conversation_templates__template_responses__completion_date',
                                    verbose_name='Last Response')
    attempts_left = tables.Column(verbose_name='Attempts Left')
    feedback = tables.TemplateColumn(verbose_name='',
                                     template_name='feedback/view_feedback_button.html',
                                     extra_context={"new_feedback": lambda record: True if record.new_feedback
                                     else False})


class ModalFeedbackTable(tables.Table):
    """
    Table of dates where responses were completed and a button to view the feedback on them
    """
    completion_date = tables.Column(verbose_name='Completion Date', accessor='completion_date', orderable=False)
    altered_rating = tables.Column(verbose_name= 'Self Rating', accessor= 'self_rating_to_string', orderable=False)
    feedback = tables.TemplateColumn(verbose_name='', template_name='feedback/select_feedback_button.html',
                                     orderable=False)
    class Meta:
        fields = ['completion_date', 'altered_rating', 'feedback']
        model = TemplateResponse


@user_passes_test(is_student)
def student_view(request):
    """
    Creates table of the student's assigned templates with links to start new responses.
    :param request:
    :return: student_view.html with table
    """
    incomplete_templates = []
    completed_templates = []
    # get the Student object matching logged in student
    student = Student.objects.filter(id=request.user.id)
    # get the assignments for that student
    now = datetime.datetime.now(get_localzone())
    assignments = Assignment.objects.filter(students=student.first()).filter(date_assigned__lte=now)
    # for each assignment, get all templates contained. Get most recent response by the student for each template
    for assignment in assignments:
        templates_in_assignment = ConversationTemplate.objects.filter(assignments=assignment, archived=False)
        for template in templates_in_assignment:
            responses = TemplateResponse.objects.filter(assignment=assignment, template=template,
                                                            student=student.first())
            last_response = responses.aggregate(Max('completion_date'))
            attempts_left = assignment.response_attempts - len(responses)
            new_feedback = False
            for feedback in responses:
                if not feedback.feedback_read:
                    new_feedback = True
                    break

            if attempts_left < 0:
                attempts_left = 0

            assigned_template_row = {}
            assigned_template_row.update({"conversation_templates__id": template.id,
                                          "id": assignment.id,
                                          "conversation_templates__name": template.name,
                                          "date_assigned": assignment.date_assigned,
                                          "conversation_templates__template_responses__completion_date":
                                              last_response['completion_date__max'],
                                          "attempts_left": attempts_left,
                                          "new_feedback": new_feedback
                                          })
            if last_response['completion_date__max'] is None and attempts_left > 0:
                incomplete_templates.append(assigned_template_row)
            else:
                completed_templates.append(assigned_template_row)

    incomplete_templates_table = IncompleteTemplatesTable(incomplete_templates, prefix="-1")
    completed_templates_table = CompletedTemplatesTable(completed_templates, prefix="-2")
    RequestConfig(request, paginate={"per_page": 10}).configure(incomplete_templates_table)
    RequestConfig(request, paginate={"per_page": 10}).configure(completed_templates_table)
    return render(request, 'student_view.html', {'incomplete_table': incomplete_templates_table,
                                                 'completed_table': completed_templates_table})


def select_feedback_view(request, pk_assignment, pk_template):
    student = Student.objects.filter(id=request.user.id)
    assignment = Assignment.objects.filter(pk=pk_assignment)
    template = ConversationTemplate.objects.filter(pk=pk_template, assignments=assignment.first())
    responses = TemplateResponse.objects.filter(student=student.first(), assignment=assignment.first(),
                                                template=template.first())
    feedback_table = ModalFeedbackTable(responses)
    return render(request, 'feedback/view_feedback_modal.html', {'table': feedback_table})
