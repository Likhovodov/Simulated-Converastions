from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from tzlocal import get_localzone
from users.models import Email, Student
import datetime


class Command(BaseCommand):
    help = "Runs scheduler for SimCon."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=get_localzone())
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            notify_students,
            trigger=CronTrigger(minute="*/1"),  # Once a minute
            id="notify_students",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        try:
            scheduler.start()
        except KeyboardInterrupt:
            scheduler.shutdown()


def notify_students():
    """
    Sends emails for assignments that are past their assigned datetime.
    :return:
    """
    time_now = datetime.datetime.now(get_localzone())
    emails_to_send = Email.objects.all()
    for email in emails_to_send:
        if email.assignment.date_assigned <= time_now:
            send_mail(subject=email.subject,
                      message=email.message,
                      recipient_list=Student.objects.filter(assignments=email.assignment),
                      from_email=None,
                      fail_silently=False)
            email.delete()