from django.db import models
import uuid


class TemplateFolder(models.Model):
    """
    A Folder containing (only) templates

    Fields:
    id: UUID to uniquely identify a folder. Primary Key
    name: Name of the folder
    templates: Templates associated to the folder.
        Templates can be associated to more than one file.

    """
    id = models.UUIDField(unique=True, editable=False, primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=40)
    templates = models.ManyToManyField('conversation_templates.ConversationTemplate', related_name='folder', blank=True)
    researcher = models.ForeignKey('users.Researcher', related_name='template_folder', default=0, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['researcher', 'name'], name='unique_folders')
        ]

    def create_folder(self, name, researcher):
        self.name = name
        self.researcher = researcher
        self.save()
        return self

    def __str__(self):
        return self.name
