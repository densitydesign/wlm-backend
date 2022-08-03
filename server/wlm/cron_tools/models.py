from datetime import datetime
from croniter import croniter
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User =  get_user_model()

class Job(models.Model):
    execution_time = models.DateTimeField(null=True, blank=True)
    cron_expression = models.CharField(null=True, blank=True, max_length=100)
    job_type = models.CharField(max_length=100)
    kwargs = models.JSONField(blank=True, default=dict)
    tag = models.CharField(max_length=100, default="", blank=True)

    def __str__(self):
        to_str = "%s " % (self.job_type,)
        if self.execution_time:
            to_str += "at %s" % (
                timezone.make_naive(self.execution_time).strftime("%d/%m/%Y %H:%M:%S"),
            )
        elif self.cron_expression:
            to_str += "cron %s" % (self.cron_expression,)
        return to_str

    def get_next_time_local(self):
        """
        Get next execution time in local timezone
        """
        if self.execution_time:
            return timezone.make_naive(self.execution_time)
        start = timezone.make_naive(timezone.localtime())
        c = croniter(self.cron_expression, start)
        return c.get_next(datetime)