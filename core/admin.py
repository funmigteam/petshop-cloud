from django.contrib import admin

from .models import Category, JoinRequest, Payment, Plan, Product, Shop, SiteConfig


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "owner", "is_active", "is_featured", "subscription_until", "views"]
    list_filter = ["is_active", "is_featured", "city"]
    search_fields = ["name", "slug", "owner__username", "phone"]
    inlines = [CategoryInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "shop", "category", "is_available", "is_featured"]
    list_filter = ["is_available", "shop"]
    search_fields = ["name", "brand"]


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "days", "price", "is_active", "is_popular", "order"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["shop", "plan", "amount", "status", "gateway", "purchase_id", "created_at", "paid_at"]
    list_filter = ["status", "gateway"]
    search_fields = ["shop__name", "purchase_id", "reference"]


admin.site.register(JoinRequest)
admin.site.register(SiteConfig)
