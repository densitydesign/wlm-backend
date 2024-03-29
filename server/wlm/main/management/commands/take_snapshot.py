from main.helpers import take_snapshot
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Takes new snapshot'

    def add_arguments(self, parser):
        parser.add_argument('--skip-pictures', action='store_true', required=False)
        parser.add_argument('--skip-geo', action='store_true', required=False)
        parser.add_argument('--category-only', action='store_true', required=False)
        #parser.add_argument('--dry-run', action='store_true', required=False)
        parser.add_argument('--force-restart', action='store_true', required=False)

    def handle(self, *args, **options):
        take_snapshot(skip_pictures=options['skip_pictures'], skip_geo=options['skip_geo'], force_restart=options['force_restart'], category_only=options['category_only'])



#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)