from django.db import models
from django.utils import timezone
import uuid


class ConversationTemplate(models.Model):
    """
    Contains information related to an entire conversation template.
    
    Fields:
    id: UUID to uniquely identify a template. Primary Key.
    name: The name given to a template
    description: The description of the template
    creation_date: The date the template was created.
    researcher: The researcher who created the template. Many to One (ForeignKey) relationship.
        Deleting a researcher deletes any templates they created.
    """
    id = models.UUIDField(unique=True, editable=False, primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=4000)
    creation_date = models.DateTimeField(default=timezone.now)
    researcher = models.ForeignKey('users.Researcher', related_name='templates', default=0, on_delete=models.CASCADE)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"
