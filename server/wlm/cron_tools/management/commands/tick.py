import logging
from sentry_sdk import capture_exception, push_scope
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils import timezone
from django.core.management.base import BaseCommand
from cronex import CronExpression
from django.conf import settings
from cron_tools.models import Job

logger = logging.getLogger('cron')

class Command(BaseCommand):
    help = "Tick and execute jobs"

    def handle(self, *args, **options):
        time_tuple = timezone.localtime().timetuple()[:5]
        self.stdout.write("Tick for time: %s" % (time_tuple,))

        for job in Job.objects.all():
            # Should Run job?
            if job.execution_time:
                now = timezone.now()
                if now < job.execution_time:
                    continue
            else:
                try:
                    cron_expr = CronExpression(job.cron_expression)
                except:
                    logger.exception("Bad cron expression %s" % (job.cron_expression,))
                    continue
                if not cron_expr.check_trigger(time_tuple):
                    continue

            # Ty to grab the related handler
            try:
                handler_location = settings.CRON_JOB_HANLDERS[job.job_type]
            except KeyError:
                self.stderr.write("%s not registered" % (job.job_type,))
                continue

            try:
                handler = import_string(handler_location)
            except ImportError:
                logger.exception(
                    "Bad handler %s for job type %s"
                    % (
                        handler_location,
                        job.job_type,
                    )
                )
                continue

            # If the job has an execution time delete them
            if job.execution_time:
                job.delete()

            try:
                handler(**job.kwargs)
            except Exception as e:
                with push_scope() as scope:
                    scope.set_tag("job_type", job.job_type)
                    scope.set_context(
                        "JobInfo",
                        {
                            "job_type": job.job_type,
                            "cron_expression": job.cron_expression,
                            "kwargs": job.kwargs,
                        },
                    )
                    capture_exception(e)
                logger.exception("Error during handling job %s" % (job.job_type,))
                # Re insert the job if is a job with time
                if job.execution_time:
                    job.pk = None
                    job.save()
