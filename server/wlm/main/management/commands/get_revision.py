from turtle import update
from main.wiki_api import get_revision
from main.helpers import update_image
from main.models import Monument
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Takes new snapshot'

    def add_arguments(self, parser):
        parser.add_argument('q', type=str)

    def handle(self, *args, **options):
        
        mon = Monument.objects.get(q_number=options['q'])
        rev = get_revision(mon.q_number)
        print(rev)

        



#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)