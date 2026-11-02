from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_shop_lat_shop_lng_shop_qr_caption"),
    ]

    operations = [
        migrations.AddField(
            model_name="shop",
            name="subscription_started_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="تاریخ فعال‌سازی اشتراک"),
        ),
    ]
