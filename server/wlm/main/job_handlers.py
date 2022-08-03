import django_rq
from main.helpers import take_snapshot
from rq import Retry
import logging 

logger = logging.getLogger(__name__)


def enqueue_take_snapshot():
    logger.info("Enqueuing take_snapshot")
    django_rq.enqueue(take_snapshot, retry=Retry(max=3), job_timeout=60 * 60 * 24)