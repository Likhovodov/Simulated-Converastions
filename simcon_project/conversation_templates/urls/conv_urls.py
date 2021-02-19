from django.urls import path
from conversation_templates.views import *

urlpatterns = [
    path('start/<uuid:ct_id>/<uuid:assign_id>/', conversation_start, name='conversation-start'),
    path('video/<uuid:ct_node_id>/', conversation_video, name='conversation-video'),
    path('choice/<uuid:ct_node_id>/', conversation_choice, name='conversation-choice'),
    path('end/<uuid:ct_response_id>/', conversation_end, name='conversation-end'),
    path('save-audio', save_audio, name='save-audio'),
    path('exit', exit_conversation, name='exit-conversation'),
]
