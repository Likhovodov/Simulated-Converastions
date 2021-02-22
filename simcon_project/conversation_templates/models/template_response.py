from django.db import models
from django.urls import reverse
import uuid


class TemplateResponse(models.Model):
    """
    Contains information for a Student response to a ConversationTemplate object

    Fields:
    id: Primary key id for TemplateResponse object
    completion_date: UTC date that Student completed conversation
    student: Student that submitted TemplateResponse object
    template: ConversationTemplate object that TemplateResponse relates to
    assignment: Assignment object that ConversationTemplate belongs to
    feedback: General feedback left by a Researcher for a Student
    self_rating: The rating a student gives their performance. Should be out of 5
    """
    id = models.UUIDField(unique=True, editable=False, primary_key=True, default=uuid.uuid4)
    completion_date = models.DateTimeField(default=None, null=True)
    student = models.ForeignKey('users.Student', related_name='template_responses', default=0, on_delete=models.CASCADE)
    template = models.ForeignKey('conversation_templates.ConversationTemplate', default=0, related_name='template_responses', on_delete=models.CASCADE)
    assignment = models.ForeignKey('users.Assignment', default=0, related_name='template_responses', on_delete=models.CASCADE)
    feedback = models.CharField(max_length=1000, default=None, null=True, blank=True)
    self_rating = models.PositiveSmallIntegerField(default=0, null=True)
    archived = models.BooleanField(default=False)
    feedback_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.email}: {self.template.name}, {self.template.researcher} ({self.completion_date})"

    def get_absolute_url(self):
        return reverse('conversation-end', kwargs={'ct_response_id': self.id})
    
    def self_rating_to_string(self):
        self_rate = ""
        if self.self_rating == 0:
            self_rate = "None"
        if self.self_rating == 1:
            self_rate = "Very unsatisfied"
        if self.self_rating == 2:
            self_rate = "Unsatisfied"
        if self.self_rating == 3:
            self_rate = "Somewhat satisfied" 
        if self.self_rating == 4:
            self_rate = "Satisfied"
        if self.self_rating == 4:
            self_rate = "Very Satisfied"
        return self_rate
