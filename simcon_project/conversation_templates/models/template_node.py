from django.db import models
from embed_video.fields import EmbedVideoField
from django.urls import reverse
import uuid


class TemplateNode(models.Model):
    """
    Contains information for a step in a conversation
    Fields:
    id: Primary key identifier for TemplateNode object
    description: Context for step in the conversation
    video_url: URL for Youtube, or Vimeo video that provides context for step in the conversation
    start: Denotes the starting point of a conversation
    terminal: Denotes an ending point of a conversation
    parent_template: ConversationTemplate object that a TemplateNode belongs to
    """
    id = models.UUIDField(unique=True, editable=False, primary_key=True, default=uuid.uuid4)
    description = models.CharField(max_length=4000)
    video_url = EmbedVideoField()
    start = models.BooleanField(default=False)
    terminal = models.BooleanField(default=False)
    parent_template = models.ForeignKey('conversation_templates.ConversationTemplate', default=0, related_name='template_nodes', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.parent_template}: {self.description}"

    def get_absolute_url(self):
        return reverse('conversation-step', kwargs={'ct_node_id': self.id})
