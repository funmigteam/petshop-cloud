from django.core.management.base import BaseCommand

from core.models import SiteConfig


class Command(BaseCommand):
    help = "Creates the site settings row if it does not exist."

    def handle(self, *args, **opts):
        SiteConfig.get()
        self.stdout.write(self.style.SUCCESS("Site settings ready."))
