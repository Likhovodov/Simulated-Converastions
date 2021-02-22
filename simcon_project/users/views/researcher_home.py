from django.shortcuts import render
from django.db.models import Q
from conversation_templates.models import TemplateResponse
from django.contrib.auth.decorators import user_passes_test
import django_tables2 as tables
from django_tables2 import RequestConfig
import functools
import operator


class ResponseTable(tables.Table):
    name = tables.columns.Column(
        accessor="student.get_full_name", order_by="student.last_name")
    altered_rating = tables.Column(verbose_name= 'Student Self Rating', accessor= 'self_rating_to_string', order_by='self_rating')
    response = tables.TemplateColumn(
        ''' <a class="btn btn btn-outline-secondary btn-sm" href="{% url 'view-response' record.id %}" >View</a>''', verbose_name='')
    delete = tables.TemplateColumn(
        '''<button class="bs-modal btn btn-outline-secondary btn-sm" type="button" name="button" data-form-url="{% url 'delete-response' record.id %}" >Delete</button>''', verbose_name='')

    class Meta:
        attrs = {'class': 'table table-sm', 'id': 'response-table'}
        model = TemplateResponse
        fields = ['template', 'name', 'completion_date',
                  'feedback', 'altered_rating', 'feedback_read']


def is_researcher(user):
    return user.is_authenticated and user.get_is_researcher()


@ user_passes_test(is_researcher)
def researcher_view(request):
    responses = TemplateResponse.objects.filter(
        template__researcher__email=request.user, archived=False)
    filtered_responses = filter_search(request, responses)

    if filtered_responses:
        response_table = ResponseTable(filtered_responses)
        RequestConfig(request, paginate={"per_page": 20}).configure(
            response_table)
    else:
        response_table = None

    context = {'responseTable': response_table}

    return render(request, 'researcher_view.html', context)


def filter_search(request, responses):
    if 'searchParam' in request.GET:
        param = request.GET['searchParam']
        if param == "":
            filter_fields = Q(student__first_name__contains=param) | Q(student__last_name__contains=param) | \
            Q(template__name__contains=param) | \
            Q(assignment__subject_labels__label_name__contains=param)
        else:
            params = param.split()
            filter_fields = functools.reduce(operator.and_, (Q(student__first_name__icontains=param) | Q(student__last_name__icontains=param) | \
            Q(template__name__icontains=param) | \
            Q(assignment__subject_labels__label_name__icontains=param) for param in params))
        responses = responses.filter(filter_fields)

    return responses
