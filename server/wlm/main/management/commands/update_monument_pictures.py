from main.helpers import update_monument, format_monument, search_commons_url, search_commons_wlm
from main.wiki_api import execute_query
from django.core.management.base import BaseCommand, CommandError
from main.models import Monument, CategorySnapshot


class Command(BaseCommand):
    help = 'Takes new snapshot'

    def add_arguments(self, parser):
        parser.add_argument('id', type=int)

    def handle(self, *args, **options):

        m = Monument.objects.get(pk=options['id'])
        print(m.relevant_images)

        for relevant_image_url in m.relevant_images:
            relevant_images_data = search_commons_url(relevant_image_url)
            print(relevant_images_data)

        if m.wlm_n:
            wlm_images_data = search_commons_wlm(m.wlm_n)
            print(len(wlm_images_data))

        
