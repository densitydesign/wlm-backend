from main.models import Monument
from django.db import models
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Gets a list of municipalities with no geo data or geo data suspect"

    def add_arguments(self, parser):
        parser.add_argument('cat', type=int)

    def handle(self, *args, **options):
        cat = options['cat']
        candidates  = Monument.objects.filter(categories__pk=cat)
        suspects = candidates.exclude(
            label=models.F('municipality__name')
        )
        self.stdout.write(self.style.SUCCESS(f"Wikidata label, Attributed municipality"))
        for item in suspects:
            municipality_label = None
            if item.municipality:
                municipality_label = item.municipality.name
            self.stdout.write(self.style.SUCCESS(f"{item.label}, {municipality_label}"))



# self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
# raise CommandError('Poll "%s" does not exist' % poll_id)
