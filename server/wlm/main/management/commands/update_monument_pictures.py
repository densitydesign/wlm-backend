from main.helpers import search_commons_wlm, update_image
from main.wiki_api import search_commons_cat
from django.core.management.base import BaseCommand
from main.models import Monument


class Command(BaseCommand):
    help = 'Takes new snapshot'

    def add_arguments(self, parser):
        parser.add_argument('id', type=int)

    def handle(self, *args, **options):

        m = Monument.objects.get(pk=options['id'])
        #print(m.relevant_images)

        if m.data.get("commons_n"):
            for cat in m.data.get("commons_n"):
                commons_image_data = search_commons_cat(cat)
                for image in commons_image_data:
                    title = image.get("title", "")
                    if title:
                        title = title.split("File:")[-1]
                    else:
                        continue
                    
                    is_relevant = False
                    for relevant_image_url in m.relevant_images:
                        file_path = relevant_image_url.split("FilePath/")[-1]
                        if title == file_path:
                            is_relevant = True
                            break
                    update_image(m, image, "commons", is_relevant)


        if m.wlm_n:
            wlm_pics_collected = 0
            wlm_images_data = search_commons_wlm(m.wlm_n)
            for image in wlm_images_data:
                update_image(m, image, "wlm")
                wlm_pics_collected += 1
        
            m.pictures_wlm_count = wlm_pics_collected
            m.save()

        
