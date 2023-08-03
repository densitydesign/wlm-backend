from django.core.management.base import BaseCommand, CommandError
from wlm_app_api.helpers import get_upload_categories




class Command(BaseCommand):
    """
    management command that wraps the get_upload_categories helper
    """    

    
    def add_arguments(self, parser):
        parser.add_argument('q_number', type=str)
        
        

    def handle(self, *args, **options):
        
        q_number = options['q_number']
        categories = get_upload_categories(q_number)
        print(categories)

        
