import os
import django_tables2 as tables
import secrets
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import HttpResponseNotFound, HttpResponse
from conversation_templates.models import ConversationTemplate, TemplateNode, TemplateNodeResponse, TemplateResponse
from conversation_templates.forms import TemplateNodeChoiceForm
from users.models import Student, Assignment
from django.contrib.auth.decorators import user_passes_test
from users.views.student_home import is_student

# Globals
ct_templates_dir = 'conversation'


class NodeDescriptionTable(tables.Table):
    """
    Creates table that displays the description for each TemplateNode object that a Student visited.
    """
    position = tables.Column(accessor='position_in_sequence')
    description = tables.Column(accessor='template_node__description')


def if_visited(request, ct_node_id):
    page_dict = request.session.get('page_dict')
    if not page_dict:
        return False
    if page_dict.get(str(ct_node_id)):
        return True
    return False


def get_node_response(request, ct_node_id):
    page_dict = request.session.get('page_dict')
    return TemplateNodeResponse.objects.get(id=page_dict.get(str(ct_node_id)))


# Tracks completed node responses
def store_node_response(request, ct_node_id, ct_node_response_id):
    page_dict = request.session.get('page_dict')
    page_dict.update({str(ct_node_id): str(ct_node_response_id)})
    request.session.modified = True


# Clear things from past user session
def flush_session_data(request):
    if 'page_dict' in request.session:
        del request.session['page_dict']
    if 'ct_response_id' in request.session:
        del request.session['ct_response_id']
    if 'ct_node_response_id' in request.session:
        del request.session['ct_node_response_id']
    if 'validation_key' in request.session:
        del request.session['validation_key']
    request.session.modified = True


def check_page_authorization(request):
    if request.session.get('validation_key') is None:
        return HttpResponseNotFound('<h1>Access Denied</h1>')


@user_passes_test(is_student)
def conversation_start(request, ct_id, assign_id):
    """
    Renders entry page for a conversation. Student can choose to start the conversation or go back.
    """
    # Check if user has retries
    assignment = Assignment.objects.get(id=assign_id)
    ct = ConversationTemplate.objects.get(id=ct_id)
    student = Student.objects.get(email=request.user)
    student_attempts = TemplateResponse.objects.filter(student=student, template=ct).count()
    if student_attempts >= assignment.response_attempts:
        return HttpResponseNotFound('<h1>Sorry, maximum number of attempts reached for this conversation.</h1>')

    # Else, set up conversation
    ctx = {}
    t = '{}/conversation_start.html'.format(ct_templates_dir)
    ct = ConversationTemplate.objects.get(id=ct_id)
    ct_start_node = TemplateNode.objects.get(parent_template=ct, start=True)

    # Clear existing session data leftover from incomplete response
    flush_session_data(request)
    request.session['assign_id'] = assign_id
    request.session['page_dict'] = {}
    request.session['validation_key'] = secrets.token_hex(8)
    request.session['allow_typed_response'] = assignment.allow_typed_response
    request.session['allow_self_rating'] = assignment.allow_self_rating
    request.session['recording_attempts'] = assignment.recording_attempts
    request.session.modified = True
    ctx.update({
        'ct': ct,
        'ct_start_node': ct_start_node,
    })
    return render(request, t, ctx)


@user_passes_test(is_student)
def conversation_video(request, ct_node_id):
    # Check to make sure student didn't copy paste old conversation link
    check_page_authorization(request)

    # Else, set up TemplateNode data
    ctx = {}
    t = '{}/conversation_video.html'.format(ct_templates_dir)
    ct_node = TemplateNode.objects.get(id=ct_node_id)
    ct_node_response = TemplateNodeResponse.objects.filter(id=request.session.get('ct_node_response_id')).first()
    ct = ct_node.parent_template
    recording_attempts = request.session['recording_attempts']

    # Check for page refresh
    if ct_node.start and request.session.get('ct_response_id') is None:
        ct_response = TemplateResponse.objects.create(
            student=Student.objects.get(email=request.user),
            template=ct,
            assignment=Assignment.objects.get(id=request.session.get('assign_id')),
        )
        request.session['ct_response_id'] = str(ct_response.id)  # persist the template response in the session
        request.session.modified = True

    ctx.update({
        'ct': ct,
        'ct_node': ct_node,
        'ct_node_response': ct_node_response,
        'recording_attempts': recording_attempts,
    })
    return render(request, t, ctx)


@user_passes_test(is_student)
def conversation_choice(request, ct_node_id):
    """
    Renders each step in a conversation where a Student can watch the video, record a response,
    and select a choice.
    """
    # Check to make sure student didn't copy paste old conversation link
    check_page_authorization(request)

    # Else, set up TemplateNode data
    ctx = {}
    t = '{}/conversation_choice.html'.format(ct_templates_dir)
    ct_node = TemplateNode.objects.get(id=ct_node_id)
    ct = ct_node.parent_template
    ct_node_response = TemplateNodeResponse.objects.filter(id=request.session.get('ct_node_response_id')).first()
    allow_typed_response = request.session['allow_typed_response']
    recording_attempts = request.session['recording_attempts']

    # Check if page has already been completed
    if not ct_node_response:
        ct_node_response = get_node_response(request, ct_node_id)

    # POST request
    if request.method == 'POST':
        ct_response = TemplateResponse.objects.filter(id=request.session.get('ct_response_id')).first()
        if not ct_response:
            # For debugging, will remove once in production
            return HttpResponseNotFound('<h1>Conversation Template Response does not exist for current session</h1>')

        choice = ct_node_response.selected_choice
        # Check if user has not submitted a choice yet
        if not choice:
            choice_form = TemplateNodeChoiceForm(
                request.POST,
                ct_node=ct_node,
                allow_typed_response=allow_typed_response
            )
            if choice_form.is_valid():
                if request.POST.get('choices') == 'custom-response':
                    custom_response = request.POST.get('custom-text')
                else:
                    custom_response = None
                    choice = choice_form.cleaned_data['choices']

                # Edit node response to add remaining fields
                ct_node_response.template_node = ct_node
                ct_node_response.selected_choice = choice
                ct_node_response.custom_response = custom_response
                ct_node_response.save()

                # Persist that node response id
                store_node_response(request, ct_node_id, ct_node_response.id)
                del request.session['ct_node_response_id']
                request.session.modified = True
            else:
                # For debugging, will be removed or changed before deploying to production
                return HttpResponseNotFound('<h1>An invalid choice was selected</h1>')

        # End conversation or go to next node
        if ct_node.terminal or choice.destination_node is None or choice is None:
            return redirect('conversation-end', ct_response_id=ct_response.id)
        return redirect('conversation-video', ct_node_id=choice.destination_node.id)

    # GET request
    choice_form = TemplateNodeChoiceForm(ct_node=ct_node, allow_typed_response=allow_typed_response)

    ctx.update({
        'ct': ct,
        'ct_node': ct_node,
        'choice_form': choice_form,
        'ct_node_response': ct_node_response,
        'allow_typed_response': allow_typed_response,
        'recording_attempts': recording_attempts,
    })
    return render(request, t, ctx)


def save_audio(request):
    data = request.FILES.get('data')
    file_handle = str(timezone.now())
    file_handle = file_handle.replace(':', '-') + '.wav'
    file_handle = os.path.join('audio', str(request.user), file_handle)  # Create full file handle
    audio_path = default_storage.save(file_handle, data)  # Store audio in media root
    ct_response = TemplateResponse.objects.get(id=request.session.get('ct_response_id'))

    # Check if node response already exists
    if request.session.get('ct_node_response_id') is None:
        ct_node_response = TemplateNodeResponse.objects.create(
            template_node=None,
            parent_template_response=ct_response,
            selected_choice=None,
            position_in_sequence=ct_response.node_responses.count() + 1,
            audio_response=audio_path
        )
        request.session['ct_node_response_id'] = ct_node_response.id
    else:
        ct_node_response = TemplateNodeResponse.objects.get(id=request.session.get('ct_node_response_id'))
        ct_node_response.audio_response = audio_path
        ct_node_response.save()
    return HttpResponse('saved')


@user_passes_test(is_student)
def conversation_end(request, ct_response_id):
    ctx = {}
    t = '{}/conversation_end.html'.format(ct_templates_dir)
    ct_response = TemplateResponse.objects.get(id=ct_response_id)
    ct = ct_response.template
    assignment = Assignment.objects.get(id=request.session.get('assign_id'))
    allow_self_rating = assignment.allow_self_rating

    # Get responses in order
    ct_node_responses = TemplateNodeResponse.objects.filter(parent_template_response=ct_response) \
        .order_by('position_in_sequence')
    response_table_content = ct_node_responses.values(
        'position_in_sequence',
        'template_node__description',
        'audio_response'
    )
    ct_node_table = NodeDescriptionTable(response_table_content)

    # POST request
    if request.method == 'POST':
        print(request.POST)
        for response in ct_node_responses:
            response.transcription = request.POST.get(str(response.id), '')
            response.save()
        # The key has to be 0, I have no clue why, just don't touch it
        if allow_self_rating:
            ct_response.self_rating = request.POST.get('0', 0)
        else:
            ct_response.self_rating = 0
        ct_response.save()
        if ct_response.completion_date is None:
            ct_response.completion_date = timezone.now()
            ct_response.save()
        return redirect('student-view')

    # GET request
    if 'validation_key' in request.session:
        del request.session['validation_key']
        request.session.modified = True
    ctx.update({
        'ct': ct,
        'ct_response': ct_response,
        'ct_node_table': ct_node_table,
        'ct_node_responses': ct_node_responses,
        'allow_self_rating': allow_self_rating
    })
    return render(request, t, ctx)


def exit_conversation(request):
    if request.is_ajax():
        ctx = {}
        t = '{}/exit_conversation_modal.html'.format(ct_templates_dir)
        return render(request, t, ctx)
    return redirect('student-view')
