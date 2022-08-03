from main.helpers import update_geo_cache
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Updates geo data and link from monuments to municipalities'


    def handle(self, *args, **options):
        update_geo_cache()



#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)