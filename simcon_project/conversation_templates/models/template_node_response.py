from django.db import models
import uuid


class TemplateNodeResponse(models.Model):
    """
    Contains information related to a user response for a TemplateNode
    Fields:
    id: Primary key id for TemplateNodeResponse object
    transcription: Student transcription of their audio_response
    template_node: TemplateNode object that student responded to
    parent_template_response: TemplateResponse that a TemplateNodeResponse object belongs to
    selected_choice: The choice the user selected for a TemplateNode
    position_in_sequence: Determines the order that TemplateNodeResponse transcriptions appear in
    feedback: Feedback left by a Researcher for Student
    audio_response: Audio recording of Student response
    """
    id = models.UUIDField(unique=True, editable=False, primary_key=True, default=uuid.uuid4)
    transcription = models.CharField(max_length=1000, null=True, blank=True)
    template_node = models.ForeignKey('conversation_templates.TemplateNode', default=0, related_name='responses', on_delete=models.DO_NOTHING)
    parent_template_response = models.ForeignKey('conversation_templates.TemplateResponse', default=0, related_name='node_responses', on_delete=models.CASCADE)
    selected_choice = models.ForeignKey('conversation_templates.TemplateNodeChoice', default=0, related_name='node_response', on_delete=models.DO_NOTHING)
    position_in_sequence = models.IntegerField()
    feedback = models.CharField(max_length=1000, default=None, null=True, blank=True)
    audio_response = models.FileField(upload_to='audio/%Y/%m/%d', default=None)

    def __str__(self):
        return self.transcription
