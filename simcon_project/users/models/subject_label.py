from django.db import models
import uuid


class SubjectLabel(models.Model):
    id = models.UUIDField(unique=True, editable=False, primary_key=True, default=uuid.uuid4)
    label_name = models.CharField(max_length=100, default=None)
    students = models.ManyToManyField('users.Student', related_name='labels', blank=True)
    researcher = models.ForeignKey('users.Researcher', related_name='labels', default=0, on_delete=models.CASCADE)

    def get_label_name(self):
        return self.label_name

    def create_label(self, name, res, **extra_fields):
        """
        Create and save a label
        """
        self.label_name = name
        self.researcher = res
        self.save()
        return self
