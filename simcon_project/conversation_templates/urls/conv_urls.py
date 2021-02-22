from django.urls import path
from conversation_templates.views import *

urlpatterns = [
    path('start/<uuid:ct_id>/<uuid:assign_id>/', conversation_start, name='conversation-start'),
    path('step/<uuid:ct_node_id>/', conversation_step, name='conversation-step'),
    path('end/<uuid:ct_response_id>/', conversation_end, name='conversation-end'),
    path('save-audio', save_audio, name='save-audio'),
    path('exit', exit_conversation, name='exit-conversation'),
]
