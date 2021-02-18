from django.db import models
import uuid
from json import JSONEncoder
from uuid import UUID

JSONEncoder_olddefault = JSONEncoder.default


def JSONEncoder_newdefault(self, o):
    if isinstance(o, UUID):
        return str(o)
    return JSONEncoder_olddefault(self, o)


JSONEncoder.default = JSONEncoder_newdefault


class Assignment(models.Model):
    id = models.UUIDField(unique=True, editable=False, primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100) 
    date_assigned = models.DateField()
    response_attempts = models.PositiveSmallIntegerField(default=1, blank=False)
    conversation_templates = models.ManyToManyField('conversation_templates.ConversationTemplate', related_name='assignments')
    students = models.ManyToManyField('users.Student', related_name='assignments')
    researcher = models.ForeignKey('users.Researcher', default=0, related_name='assignments', on_delete=models.CASCADE)
    subject_labels = models.ManyToManyField('users.SubjectLabel', related_name='assignments', blank=True)
    recording_attempts = models.PositiveSmallIntegerField(default=1, blank=False)
    allow_typed_response = models.BooleanField(default=False)
    allow_self_rating = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}, {self.researcher}, ({self.date_assigned})"

    def get_name(self):
        return self.name

    def get_date_assigned(self):
        return self.date_assigned
