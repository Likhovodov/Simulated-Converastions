from django.db import models
import uuid


class Email(models.Model):
    id = models.UUIDField(unique=True, editable=False, primary_key=True, default=uuid.uuid4)
    subject = models.CharField(max_length=100, default=None)
    message = models.CharField(max_length=500, default=None)
    assignment = models.OneToOneField('users.Assignment', related_name='email', on_delete=models.CASCADE)