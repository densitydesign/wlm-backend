from main.helpers import update_monument, format_monument
from main.wiki_api import execute_query
from django.core.management.base import BaseCommand, CommandError
from main.models import Monument, CategorySnapshot


class Command(BaseCommand):
    help = 'Takes new snapshot'

    def add_arguments(self, parser):
        parser.add_argument('q', type=str)
        parser.add_argument('catsnapshot', type=int)

        parser.add_argument('--skip-pictures', action='store_true', required=False)
        parser.add_argument('--skip-geo', action='store_true', required=False)
        parser.add_argument('--category-only', action='store_true', required=False)
        #parser.add_argument('--dry-run', action='store_true', required=False)
        parser.add_argument('--reset-pictures', action='store_true', required=False)

    def handle(self, *args, **options):

        c = CategorySnapshot.objects.get(pk=options['catsnapshot'])
        if not c.query:
            print("no query")
            return 
        if(not c.payload):
            results = execute_query(c.query)
            data = results["results"]["bindings"]
            c.payload = data
            c.save()
        
        
        monuments = [format_monument(x) for x in c.payload]
        mons = [x for x in monuments if x['mon'] == options['q']]
        if len(mons) == 0:
            print("No monument found")
            return
        mon = mons[0]

        update_monument(mon, c, skip_pictures=options['skip_pictures'], skip_geo=options['skip_geo'], reset_pictures=options['reset_pictures'], category_only=options['category_only'])



#self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
#raise CommandError('Poll "%s" does not exist' % poll_id)