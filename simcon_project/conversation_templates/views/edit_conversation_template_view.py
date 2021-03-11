import json
from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponse
from django.contrib.auth.decorators import user_passes_test
from users.views.researcher_home import is_researcher
from django.views.decorators.csrf import ensure_csrf_cookie
from conversation_templates.models import TemplateNodeChoice, TemplateNode, ConversationTemplate
from users.models import Researcher


@user_passes_test(is_researcher)
@ensure_csrf_cookie  # guarantees csrf cookie is generated even though html does not contain {% csrf_token %}
def edit_conversation_template(request, pk):

    try:
        conversation_template = ConversationTemplate.objects.get(id = pk)
        if conversation_template.researcher != Researcher.objects.get(email=request.user.email):
            return HttpResponse(status=401)

        template_nodes = TemplateNode.objects.filter(parent_template=conversation_template)
        model_JSON = json.dumps({
            'name' : conversation_template.name,
            'description' : conversation_template.description,
            'example_conversation' : conversation_template.example_conversation,
            'nodes' : [
                {
                    'id' : node.id,
                    'name' : node.name,
                    'description' : node.description,
                    'video_url' : node.video_url,
                    'start' : node.start,
                    'terminal' : node.terminal,
                    'choices' : [
                        {
                            'choice_text' : choice.choice_text,
                            'choice_destination' : "" if not choice.destination_node else choice.destination_node.id
                        } for choice in TemplateNodeChoice.objects.filter(parent_template_node=node)
                    ]
                } for node in template_nodes
            ]
        })
        return render(request, 'template_management/create_conversation_template.html', {'modelObject' : model_JSON })
    except ConversationTemplate.DoesNotExist:
        return HttpResponseNotFound()

