import django_rq
from main.helpers import take_snapshot
from rq import Retry
import logging

logger = logging.getLogger(__name__)


def enqueue_take_snapshot():
    logger.info("Enqueuing take_snapshot")
    django_rq.enqueue(
        take_snapshot,
        # retry=Retry(max=1),
        job_timeout=60 * 60 * 24,
    )


def enqueue_take_snapshot_reset_pics():
    logger.info("Enqueuing enqueue_take_snapshot_reset_pics")
    django_rq.enqueue(
        take_snapshot,
        kwargs={"reset_pictures": True},
        # retry=Retry(max=1),
        job_timeout=60 * 60 * 24,
    )
