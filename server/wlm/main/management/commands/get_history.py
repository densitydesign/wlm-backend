from turtle import update
from main.models import Region
from django.core.management.base import BaseCommand, CommandError
from main.helpers import get_date_snap_wlm
import datetime


def get_date(value):
    return datetime.datetime.strptime(value, "%Y-%m-%d")

def region(value):
    return Region.objects.get(name__iexact=value)

class Command(BaseCommand):
    help = 'Takes new snapshot'

    def add_arguments(self, parser):
        parser.add_argument('region', type=region)
        parser.add_argument('date', type=get_date)
        

    def handle(self, *args, **options):
        
        reg = options['region']
        monuments = reg.monuments.all()
        snap = get_date_snap_wlm(monuments, options['date'])
        print(snap)
        



#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)