from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django_tables2 import tables, RequestConfig, SingleTableView
from django_tables2.export.views import TableExport
from conversation_templates.models import ConversationTemplate, TemplateResponse
from conversation_templates.forms import SelectTemplateForm


class ResponseTable(tables.Table):
    name = tables.columns.Column()

    class Meta:
        attrs = {'id': 'excel-table'}
        model = TemplateResponse
        fields = ['assignment', 'student_name', 'completion_date']


class TemplateResponsesView(UserPassesTestMixin, LoginRequiredMixin, SingleTableView):
    model = TemplateResponse
    table_class = ResponseTable
    template_name = "template_all_responses_view.html"

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_researcher

    def get(self, request, pk):
        """
        On get request render a custom table based on ResponseTable:
        Rows: all template responses for the conversation template
        Columns: student.first_name, student.last_name, template_response.completion_date,
                 and template_node_responses with template_node.description as headers (this is
                 dynamically created since each template has different number of nodes")
        """
        template = ConversationTemplate.objects.get(pk=pk)
        extra_columns = []  # List of tuples of description and column object to pass to table
        table_data = []  # List of dictionaries to populate table. 1 dictionary = 1 column

        for idx, node in enumerate(template.template_nodes.all().order_by('position_in_sequence')):
            if node.terminal:
                extra_columns.append((node.description, tables.columns.Column(
                    orderable=False, attrs={'th': {'class': 'data-column'}},
                    verbose_name=f'{idx + 1}: {node.description} (Terminal)')))
            else:
                extra_columns.append((node.description, tables.columns.Column(
                    orderable=False, attrs={'th': {'class': 'data-column'}},
                    verbose_name=f'{idx + 1}: {node.description}')))

        extra_columns.append(("rating", tables.columns.Column(default=False)))
        extra_columns.append(
            ("custom_response", tables.columns.BooleanColumn(default=False, verbose_name="Custom End")))

        # Populate the table with data for each response
        completed_responses = template.template_responses.exclude(completion_date__isnull=True)
        for response in completed_responses.order_by('-completion_date'):
            column_data = {
                "assignment": response.assignment.name,
                "student_name": f"{response.student.last_name} {response.student.first_name}",
                "completion_date": response.completion_date,
            }

            for node in response.node_responses.all().order_by('position_in_sequence'):
                if node.custom_response:
                    column_data.update({node.template_node.description: node.transcription + ' (Custom Response)'})
                    column_data.update({"custom_response": True})
                else:
                    column_data.update({node.template_node.description: node.transcription})
                    column_data.update({"custom_response": False})

            column_data.update({"rating": response.self_rating_to_string})
            table_data.append(column_data)

        if 'filter' in request.GET:
            table_data = filter_search(request, table_data)

        if not table_data:
            response_table = None
        else:
            response_table = ResponseTable(data=table_data, extra_columns=extra_columns)
            RequestConfig(request, paginate=False).configure(response_table)


        export_format = request.GET.get("_export", None)
        context = {
            "table": response_table,
            "form": SelectTemplateForm(request=request, initial=template),
            "pk": pk
        }

        # Code needed to export table as .xls
        if TableExport.is_valid_format(export_format):
            exporter = TableExport(export_format, response_table)
            file_name = f"{template.name}.{format(export_format)}"
            return exporter.response(file_name)

        return render(request, self.template_name, context)

    def post(self, request, pk):
        # Note: keep pk even if it isn't used since the url requires it.
        # Redirect to selected template_responses_table from the choicefield
        return redirect(reverse('view-all-responses', args=[request.POST['templates']]))


def filter_search(request, table_data):
    filtered_data = []
    param = request.GET['filter']
    for data in table_data:
        # if param is in any of the key value pairs in the dictionary data.items()
        if {k: v for (k, v) in data.items() if filter_helper(k, v, param)}:
            filtered_data.append(data)
    return filtered_data


def filter_helper(k, v, param):
    exclude_params = ['completion_date', 'custom_response']
    if k not in exclude_params:
        if param.lower() in v.lower():
            return True

    return False
