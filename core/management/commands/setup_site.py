from django.core.management.base import BaseCommand

from core.models import Plan, SiteConfig

DEFAULT_PLANS = [
    ("۱۵ روزه", 15, 1_500_000, "مناسب برای امتحان کردن", False),
    ("ماهانه", 30, 2_500_000, "پرداخت ماه به ماه", True),
    ("سالانه", 365, 24_000_000, "۲ ماه رایگان نسبت به ماهانه", False),
]


class Command(BaseCommand):
    help = "Creates the default subscription plans (15-day, monthly, yearly) and site settings."

    def handle(self, *args, **opts):
        SiteConfig.get()
        for order, (name, days, price, desc, popular) in enumerate(DEFAULT_PLANS):
            _, created = Plan.objects.get_or_create(
                days=days, defaults={"name": name, "price": price, "description": desc, "is_popular": popular, "order": order},
            )
            self.stdout.write(("+ " if created else "= ") + name)
        self.stdout.write(self.style.SUCCESS("Plans ready. Edit prices in /manage/plans/."))
