from django.db import transaction
from main.helpers import update_first_image_date
from django.core.management.base import BaseCommand, CommandError



class Command(BaseCommand):
    help = 'Updates geo positions looking in parent documents'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', required=False)

    
    @transaction.atomic
    def handle(self, *args, **options):
        update_first_image_date()


#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)