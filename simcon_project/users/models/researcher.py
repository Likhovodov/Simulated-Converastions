from .custom_user import CustomUser
from .subject_label import SubjectLabel


class Researcher(CustomUser):
    def save(self, *args, **kwargs):
        if not self.pk:
            super(Researcher, self).save(*args, **kwargs)
            self.set_unusable_password()
            label = SubjectLabel().create_label('All Students', self)
        else:
            super(Researcher, self).save(*args, **kwargs)
