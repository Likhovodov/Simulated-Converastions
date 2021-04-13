from django.shortcuts import render
import django_tables2 as tables
from django_tables2.config import RequestConfig
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy
from users.views.researcher_home import is_researcher
from users.models import Assignment, Researcher, Student
from conversation_templates.models import ConversationTemplate, TemplateResponse
from bootstrap_modal_forms.generic import BSModalDeleteView


class AssignmentsTable(tables.Table):
    """
    Table for main view.
    """
    name = tables.Column(verbose_name='Name', accessor='name')
    date_assigned = tables.Column(verbose_name='Date Assigned', accessor='date_assigned')
    hamburger_button = tables.TemplateColumn(verbose_name='',
                                             template_name='assignment_management/assignment_hamburger_button.html')


class AssignmentDetailsTable(tables.Table):
    """
    Table for assignment details modal.
    """
    response_attempts = tables.Column(verbose_name='Response Attempts',
                                      accessor='response_attempts')
    recording_attempts = tables.Column(verbose_name='Recording Attempts',
                                       accessor='recording_attempts')
    allow_typed_response = tables.Column(verbose_name='Allow Typed Response',
                                         accessor='allow_typed_response')
    allow_self_rating = tables.Column(verbose_name='Allow Self Rating',
                                      accessor='allow_self_rating')


class TemplatesContainedTable(tables.Table):
    """
    Table for templates modal
    """
    name = tables.Column(verbose_name='Name',
                         accessor='name',
                         orderable=False)
    description = tables.Column(verbose_name='Description',
                                accessor='description',
                                orderable=False)
    view_responses = tables.TemplateColumn(verbose_name='',
                                           template_name='assignment_management/view_responses_button.html',
                                           orderable=False)


class AssignedStudentsTable(tables.Table):
    """
    Table for students modal
    """
    name = tables.Column(verbose_name='Name',
                         accessor='name',
                         orderable=False)
    email_address = tables.Column(verbose_name='Email Address',
                                  accessor='email_address',
                                  orderable=False)
    templates_completed = tables.Column(verbose_name='Templates Completed',
                                        accessor='templates_completed',
                                        orderable=False,
                                        attrs={'td': {'class': 'centered'}, 'th': {'class': 'centered'}})


class AssignmentDeleteView(BSModalDeleteView):
    """
    Deletes an assignment. Confirmation modal pops up to make sure
    the user wants to delete.
    """
    model = Assignment
    template_name = 'assignment_management/assignment_delete_modal.html'
    success_message = None
    success_url = reverse_lazy('ass-management:main')

    def get(self, request, *args, **kwargs):
        """
        Override post to send name of assignment that
        will be removed as context to the template
        """
        super().get(request, *args, **kwargs)
        assignment = Assignment.objects.get(pk=self.kwargs['pk'])
        context = {"assignment": assignment}
        return render(request, self.template_name, context)


@user_passes_test(is_researcher)
def assignment_management_view(request):
    """
    Main view for assignment management. Has table of researcher's assignments with modals for more info and
    option to delete.
    """
    assignment_rows = []
    researcher = Researcher.objects.get(id=request.user.id)
    assignments = Assignment.objects.filter(researcher=researcher)

    # build each row for table. one assignment per row
    for assignment in assignments:
        row_data = {}
        row_data.update({"id": assignment.id,
                        "name": assignment.name,
                         "date_assigned": assignment.date_assigned})
        assignment_rows.append(row_data)

    assignments_table = AssignmentsTable(assignment_rows)
    RequestConfig(request, paginate={"per_page": 10}).configure(assignments_table)
    return render(request, 'assignment_management/main_view.html', {'table': assignments_table})


@user_passes_test(is_researcher)
def view_settings(request, pk):
    """
    View for assignments details modal. Shows the settings for an assignment.
    """
    assignment = Assignment.objects.filter(pk=pk).first()
    if assignment is None:
        assignment_details = []
    else:
        if assignment.allow_typed_response is True:
            typed_response = "Yes"
        else:
            typed_response = "No"
        if assignment.allow_self_rating is True:
            self_rating = "Yes"
        else:
            self_rating = "No"
        assignment_details = [{"response_attempts": assignment.response_attempts,
                              "recording_attempts": assignment.recording_attempts,
                              "allow_typed_response": typed_response,
                              "allow_self_rating": self_rating}]
    assignment_details_table = AssignmentDetailsTable(assignment_details)
    return render(request, 'assignment_management/view_settings_modal.html', {'table': assignment_details_table})


@user_passes_test(is_researcher)
def view_templates(request, pk):
    """
    View for templates modal. Shows all templates in an assignment and links to excel page to see submissions.
    """
    assignment = Assignment.objects.get(pk=pk)
    templates = ConversationTemplate.objects.filter(assignments=assignment)
    # get each template in assignment. limit description to 200 total characters
    # one template per row in table.
    for template in templates:
        if len(template.description) >= 200:
            template.description = template.description[:197] + '...'
    if templates.count() <= 0:
        templates = []
    templates_contained_table = TemplatesContainedTable(templates)
    return render(request, 'assignment_management/view_templates_modal.html', {'table': templates_contained_table})


@user_passes_test(is_researcher)
def view_students(request, pk):
    """
    View for students modal. Shows students that were given assignment. Number of templates completed
    out of total assigned is shown per student and overall completion is shown.
    """
    student_rows = []
    total_completed_templates = 0
    assignment = Assignment.objects.get(pk=pk)
    students = Student.objects.filter(assignments=assignment)
    templates = ConversationTemplate.objects.filter(assignments=assignment)
    assigned_template_count = ConversationTemplate.objects.filter(assignments=assignment).count()

    # per student, count number of templates in assignment they have at least one submission for
    # as well as getting name and email. One student per row for table.
    for student in students:
        completed_template_count = TemplateResponse.objects.exclude(completion_date=None) \
                                                            .filter(assignment=assignment,
                                                                    template__in=templates,
                                                                    student=student) \
                                                            .values('template') \
                                                            .distinct().count()
        if completed_template_count > assigned_template_count:
            completed_template_count = assigned_template_count
        if completed_template_count < 0:
            completed_template_count = 0
        total_completed_templates = total_completed_templates + completed_template_count

        row_data = {}
        row_data.update({'id': student.id,
                         'name': student.first_name + ' ' + student.last_name,
                         'email_address': student.email,
                         'templates_completed': str(completed_template_count) + '/' + str(assigned_template_count)})
        student_rows.append(row_data)
    assigned_students_table = AssignedStudentsTable(student_rows)

    total_assigned_templates = ConversationTemplate.objects.filter(assignments=assignment).count() * \
                                                                        assignment.students.count()
    if total_completed_templates > total_assigned_templates:
        total_completed_templates = total_assigned_templates
    if total_completed_templates < 0:
        total_completed_templates = 0
    if total_assigned_templates <= 0:
        completion_string = 'No students were given this assignment.'
    else:
        completion_percent = total_completed_templates / total_assigned_templates
        completion_percent = str(completion_percent * 100).split('.', 1)[0] + '%'
        completion_string = completion_percent + ' of assigned templates have been completed at least once.'
    return render(request, 'assignment_management/view_students_modal.html', {'table': assigned_students_table,
                                                                               'completion_string': completion_string})
