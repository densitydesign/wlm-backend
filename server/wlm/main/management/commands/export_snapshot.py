from main.helpers import create_export
from main.wiki_api import execute_query
from django.core.management.base import BaseCommand, CommandError
from main.models import Snapshot


class Command(BaseCommand):
    help = 'creates snapshot exports'

    def add_arguments(self, parser):
        parser.add_argument('id', type=int)
        
    def handle(self, *args, **options):
        snapshot = Snapshot.objects.get(pk=options['id'])
        create_export(snapshot)

