from django.db import models
from .custom_user import CustomUser
from .subject_label import SubjectLabel


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
