from django.shortcuts import render, get_object_or_404
from users.views.redirect_from_login import is_authenticated
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.forms import UpdateFeedback
from conversation_templates.models import TemplateResponse, TemplateNodeResponse
from django.contrib.auth.decorators import user_passes_test
from users.views.researcher_home import is_researcher


@user_passes_test(is_authenticated)
def view_response(request, pk):
    response = get_object_or_404(TemplateResponse, pk=pk)
    if request.method == "POST":
        response_table = TemplateResponse.objects.all()
        items_to_delete = request.POST.getlist('delete_items')
        response_table.filter(pk__in=items_to_delete).delete()
        return HttpResponseRedirect(reverse('researcher-view'))
    nodes = []
    num_nodes = TemplateNodeResponse.objects.filter(
        parent_template_response=response).count()
    for i in range(1, num_nodes+1):
        if TemplateNodeResponse.objects.get(parent_template_response=response, position_in_sequence=i):
            nodes.append(TemplateNodeResponse.objects.get(parent_template_response=response,
                                                          position_in_sequence=i))
        else:
            break

    user = get_user_model()
    if user.get_is_researcher(request.user):
        return render(request, 'view_response.html', {'response_nodes': nodes, 'response': response})
    else:
        return render(request, 'view_feedback.html', {'response_nodes': nodes, 'response': response})


@user_passes_test(is_researcher)
def update_overall_response_feedback(request, pk):
    """Function for updating feedback on a response"""
    feedback_instance = get_object_or_404(TemplateResponse, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = UpdateFeedback(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            feedback_instance.feedback = form.cleaned_data['feedback']
            feedback_instance.save()

        # redirect to a new URL:
        return HttpResponseRedirect(reverse('view-response', kwargs={'pk': pk}))

    # If this is a GET (or any other method) create the default form.
    else:
        default_feedback = feedback_instance.feedback
        form = UpdateFeedback(initial={'feedback': default_feedback, })

    context = {
        'form': form,
        'feedback_instance': feedback_instance,
    }

    return render(request, 'update_response.html', context)


@user_passes_test(is_researcher)
def update_node_response_feedback(request, pk):
    """Function for updating feedback on a response"""
    feedback_instance = get_object_or_404(TemplateNodeResponse, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = UpdateFeedback(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            feedback_instance.feedback = form.cleaned_data['feedback']
            feedback_instance.save()

        # redirect to a new URL:
        return HttpResponseRedirect(reverse('view-response', kwargs={'pk': pk}))

    # If this is a GET (or any other method) create the default form.
    else:
        default_feedback = feedback_instance.feedback
        form = UpdateFeedback(initial={'feedback': default_feedback, })

    context = {
        'form': form,
        'feedback_instance': feedback_instance,
    }

    return render(request, 'update_node_response.html', context)
