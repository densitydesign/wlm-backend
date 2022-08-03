from django.db import transaction
from main.helpers import update_geo, update_geo_cache
from django.core.management.base import BaseCommand, CommandError



class Command(BaseCommand):
    help = 'Updates geo data and link from monuments to municipalities'

    def add_arguments(self, parser):
        parser.add_argument('regions_path', type=str)
        parser.add_argument('provinces_path', type=str)
        parser.add_argument('municipalities_path', type=str)
        parser.add_argument('--dry-run', action='store_true', required=False)

    @transaction.atomic
    def handle(self, *args, **options):
        update_geo(options['regions_path'], options['provinces_path'], options['municipalities_path'])
        update_geo_cache()



#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)