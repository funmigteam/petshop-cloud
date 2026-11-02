from django import template
from django.utils import timezone

register = template.Library()

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 + gd + g_d_m[gm - 1]
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        return jy, 1 + days // 31, 1 + days % 31
    return jy, 7 + (days - 186) // 30, 1 + (days - 186) % 30


@register.filter
def fa(value):
    if value is None:
        return ""
    return str(value).translate(_FA_DIGITS)


@register.filter
def money(value):
    try:
        return f"{int(value):,}".replace(",", "٬").translate(_FA_DIGITS)
    except (TypeError, ValueError):
        return ""


@register.filter
def jdate(value, fmt="short"):
    if not value:
        return "—"
    if hasattr(value, "hour") and timezone.is_aware(value):
        value = timezone.localtime(value)
    y, m, d = gregorian_to_jalali(value.year, value.month, value.day)
    if fmt == "long":
        out = f"{d} {_MONTHS[m - 1]} {y}"
    elif fmt == "time" and hasattr(value, "hour"):
        out = f"{y}/{m:02d}/{d:02d} — {value.hour:02d}:{value.minute:02d}"
    else:
        out = f"{y}/{m:02d}/{d:02d}"
    return out.translate(_FA_DIGITS)


@register.filter
def jmonth(value):
    y, m, _ = gregorian_to_jalali(value.year, value.month, value.day)
    return f"{_MONTHS[m - 1]}"
