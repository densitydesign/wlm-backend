from turtle import update
from main.sparql import search_commons
from main.helpers import update_image
from main.models import Monument
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Takes new snapshot'

    def add_arguments(self, parser):
        parser.add_argument('q', type=str)

    def handle(self, *args, **options):
        
        out = search_commons(options['q'])

        mon = Monument.objects.get(q_number=options['q'])
        for image in out:
            update_image(mon, image, "commons")

        



#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)