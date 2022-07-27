from main.helpers import update_geo
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Updates geo data and link from monuments to municipalities'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', required=False)

    def handle(self, *args, **options):
        print("update_geo")
        print(options)



#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)