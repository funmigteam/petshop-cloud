from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

MAIN_ADMIN_USERNAME = "arshia1020"
MAIN_ADMIN_PASSWORD = "rabet2611"


class Command(BaseCommand):
    help = "Creates (or resets) the main site admin superuser for pet-online.ir."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=MAIN_ADMIN_USERNAME)
        parser.add_argument("--password", default=MAIN_ADMIN_PASSWORD)

    def handle(self, *args, **opts):
        username = opts["username"]
        password = opts["password"]
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": True, "is_superuser": True, "is_active": True},
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS(f"+ ادمین اصلی ساخته شد: {username}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"= ادمین اصلی به‌روزرسانی شد: {username}"))
        self.stdout.write("ورود از /login/ یا /django-admin/ با همین نام کاربری و رمز.")
