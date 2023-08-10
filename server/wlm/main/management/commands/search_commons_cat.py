from turtle import update
from main.wiki_api import search_commons_cat
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Test for search_commons_url'

    def add_arguments(self, parser):
        parser.add_argument('cat', type=str)
        #parser.add_argument('--update', action='store_true', default=False)

    def handle(self, *args, **options):
        
        out = search_commons_cat(options['cat'])
        print(out)
        for x in out:
            print(x)
        
        

        



#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)