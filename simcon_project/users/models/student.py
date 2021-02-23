from django.db import models
from .custom_user import CustomUser
from .subject_label import SubjectLabel
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db.models.signals import post_save
#from django.contrib.sites.models import Site


class Student(CustomUser):
    added_by = models.ForeignKey('users.Researcher', default=0, related_name='students', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.pk:
            super(Student, self).save(*args, **kwargs)
            self.set_unusable_password()

            # adds a student to the "All Students" label
            label = SubjectLabel.objects.get(label_name="All Students", researcher=self.added_by)
            label.students.add(self)

        else:
            super(Student, self).save(*args, **kwargs)
