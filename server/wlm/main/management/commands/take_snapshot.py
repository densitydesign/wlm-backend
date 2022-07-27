from main.helpers import take_snapshot
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Takes new snapshot'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', required=False)

    def handle(self, *args, **options):
        print("take_snapshot")
        print(options)



#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)