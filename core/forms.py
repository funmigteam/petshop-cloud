import secrets

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .models import Category, JoinRequest, Plan, Product, Shop, SiteConfig

User = get_user_model()


class Styled:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault("class", "switch")
            elif isinstance(w, forms.ClearableFileInput | forms.FileInput):
                w.attrs.setdefault("class", "file-input")
                w.attrs.setdefault("accept", "image/*")
            elif isinstance(w, forms.Select):
                w.attrs.setdefault("class", "input")
            else:
                w.attrs.setdefault("class", "input")
            if isinstance(w, forms.Textarea):
                w.attrs["rows"] = 4


class LoginForm(Styled, AuthenticationForm):
    pass


SHOP_PUBLIC_FIELDS = [
    "name", "tagline", "description", "logo", "banner", "theme_color",
    "phone", "city", "address", "working_hours", "instagram",
]

class ShopSettingsForm(Styled, forms.ModelForm):

    class Meta:
        model = Shop
        fields = SHOP_PUBLIC_FIELDS
        widgets = {"theme_color": forms.TextInput(attrs={"type": "color"})}


class ShopAdminForm(Styled, forms.ModelForm):

    class Meta:
        model = Shop
        fields = ["name", "slug"] + SHOP_PUBLIC_FIELDS[1:] + ["is_active", "is_featured"]
        widgets = {"theme_color": forms.TextInput(attrs={"type": "color"})}

    def clean_slug(self):
        return self.cleaned_data["slug"].lower()


class ShopCreateForm(ShopAdminForm):
    username = forms.CharField(label="نام کاربری مالک", max_length=150, help_text="برای ورود به پنل. انگلیسی.")
    password = forms.CharField(
        label="رمز عبور", required=False, help_text="خالی بگذارید تا رمز تصادفی ساخته شود.",
    )
    initial_days = forms.IntegerField(label="اشتراک هدیه (روز)", min_value=0, initial=15)

    field_order = ["name", "slug", "username", "password", "initial_days"]

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("این نام کاربری قبلاً استفاده شده است.")
        return username

    def save(self, commit=True):
        shop = super().save(commit=False)
        self.generated_password = self.cleaned_data["password"] or secrets.token_urlsafe(8)
        shop.owner = User.objects.create_user(
            username=self.cleaned_data["username"], password=self.generated_password,
        )
        shop.save()
        if self.cleaned_data["initial_days"]:
            shop.extend(self.cleaned_data["initial_days"])
        return shop


class CategoryForm(Styled, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "icon", "order"]
        widgets = {"icon": forms.RadioSelect}


class ProductForm(Styled, forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "brand", "description", "image", "is_available", "is_featured", "order"]

    def __init__(self, *args, shop=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(shop=shop)
        self.fields["category"].empty_label = "— بدون دسته —"


class QrCaptionForm(Styled, forms.ModelForm):
    class Meta:
        model = Shop
        fields = ["qr_caption"]


class LocationForm(Styled, forms.ModelForm):
    class Meta:
        model = Shop
        fields = ["lat", "lng"]
        widgets = {"lat": forms.HiddenInput(), "lng": forms.HiddenInput()}


class PlanForm(Styled, forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["name", "days", "price", "description", "is_active", "is_popular", "order"]


class SiteConfigForm(Styled, forms.ModelForm):
    class Meta:
        model = SiteConfig
        fields = ["hero_title", "hero_subtitle", "support_phone", "about"]


class JoinRequestForm(Styled, forms.ModelForm):
    class Meta:
        model = JoinRequest
        fields = ["shop_name", "owner_name", "phone", "city", "message"]


class ExtendForm(Styled, forms.Form):
    days = forms.IntegerField(label="تعداد روز", min_value=-3650, max_value=3650, initial=30,
                              help_text="عدد منفی از اعتبار کم می‌کند.")


class SetPasswordForm(Styled, forms.Form):
    password = forms.CharField(label="رمز جدید", min_length=6, widget=forms.PasswordInput)
    password2 = forms.CharField(label="تکرار رمز", widget=forms.PasswordInput)

    def clean(self):
        data = super().clean()
        if data.get("password") != data.get("password2"):
            raise forms.ValidationError("رمزها یکسان نیستند.")
        return data
