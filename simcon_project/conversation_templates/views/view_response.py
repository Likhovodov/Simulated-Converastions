from django.shortcuts import render, get_object_or_404, redirect
from users.views.redirect_from_login import is_authenticated
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from conversation_templates.models import TemplateResponse, TemplateNodeResponse
from django.contrib.auth.decorators import user_passes_test
from bootstrap_modal_forms.generic import BSModalDeleteView
from django.core.mail import send_mail


@user_passes_test(is_authenticated)
def view_response(request, pk):
    response = get_object_or_404(TemplateResponse, pk=pk)

    user = get_user_model()
    response.response_read = True
    response.save()

    if request.method == 'POST':
        if 'update-overall-feedback' in request.POST:
            response.feedback = request.POST.get('overall-feedback-input')
            response.feedback_read = False
            response.save()
            return HttpResponseRedirect(reverse('view-response', kwargs={'pk': pk}))
        if 'update-node-transcription' in request.POST:
            nodeId = request.POST.get('template-node-response-id')
            currentNode = get_object_or_404(TemplateNodeResponse, pk=nodeId)
            currentNode.transcription = request.POST.get('node-transcription-input')
            if user.get_is_researcher(request.user):
                currentNode.transcription_student_editable = False

            currentNode.save()
            return HttpResponseRedirect(reverse('view-response', kwargs={'pk': pk}))

    nodes = []
    num_nodes = TemplateNodeResponse.objects.filter(
        parent_template_response=response).count()
    for i in range(1, num_nodes+1):
        if TemplateNodeResponse.objects.get(parent_template_response=response, position_in_sequence=i):
            nodes.append(TemplateNodeResponse.objects.get(parent_template_response=response,
                                                          position_in_sequence=i))
        else:
            break

    self_rating = ""
    if response.self_rating == 0:
        self_rating = "None"
    if response.self_rating == 1:
        self_rating = "Very unsatisfied"
    if response.self_rating == 2:
        self_rating = "Unsatisfied"
    if response.self_rating == 3:
        self_rating = "Somewhat satisfied"
    if response.self_rating == 4:
        self_rating = "Satisfied"
    if response.self_rating == 5:
        self_rating = "Very Satisfied"

    if user.get_is_researcher(request.user):
        return render(request, 'view_response.html', {'response_nodes': nodes, 'response': response, 'self_rating': self_rating})
    else:
        response.feedback_read = True
        response.save()
        return render(request, 'feedback/view_feedback.html', {'response_nodes': nodes, 'response': response, 'self_rating': self_rating})

class ResponseDeleteView(BSModalDeleteView):
    model = TemplateResponse
    template_name = 'response_delete_modal.html'
    success_message = None
    success_url = reverse_lazy('researcher-view')
    def get(self, request, pk):
        this_response = TemplateResponse.objects.get(pk=pk)
        context = {"template_name": this_response.template.name, "student": this_response.student.first_name}
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        this_response = TemplateResponse.objects.get(pk=pk)
        student_email = this_response.student.email
        if 'reassign' in request.POST:
            template_name= this_response.template.name
            subject = 'New Re-Assigned Template for Simulated Conversations: '+ template_name
            message = 'Please check your Portal to complete: '+ template_name
            send_mail(subject, message, 'smtp.gmail.com', [student_email], fail_silently=False)
        this_response.delete()
        return redirect(reverse('researcher-view'))
