from django.urls import include, path

from .views import auth, manage, panel, pay, public

panel_urls = ([
    path("", panel.dashboard, name="dashboard"),
    path("products/", panel.products, name="products"),
    path("products/new/", panel.product_form, name="product_new"),
    path("products/<int:pk>/", panel.product_form, name="product_edit"),
    path("products/<int:pk>/delete/", panel.product_delete, name="product_delete"),
    path("products/<int:pk>/toggle/", panel.product_toggle, name="product_toggle"),
    path("categories/", panel.categories, name="categories"),
    path("categories/<int:pk>/", panel.categories, name="category_edit"),
    path("categories/<int:pk>/delete/", panel.category_delete, name="category_delete"),
    path("settings/", panel.settings_view, name="settings"),
    path("location/", panel.location, name="location"),
    path("qr/", panel.qr, name="qr"),
    path("password/", panel.password, name="password"),
    path("billing/", panel.billing, name="billing"),
    path("billing/buy/<int:plan_id>/", panel.buy, name="buy"),
    path("exit/", panel.exit_acting, name="exit"),
], "panel")

manage_urls = ([
    path("", manage.dashboard, name="dashboard"),
    path("shops/", manage.shops, name="shops"),
    path("shops/new/", manage.shop_create, name="shop_new"),
    path("shops/<int:pk>/", manage.shop_detail, name="shop"),
    path("shops/<int:pk>/edit/", manage.shop_edit, name="shop_edit"),
    path("shops/<int:pk>/delete/", manage.shop_delete, name="shop_delete"),
    path("shops/<int:pk>/extend/", manage.shop_extend, name="shop_extend"),
    path("shops/<int:pk>/token/", manage.shop_token, name="shop_token"),
    path("shops/<int:pk>/toggle/", manage.shop_toggle, name="shop_toggle"),
    path("shops/<int:pk>/password/", manage.shop_password, name="shop_password"),
    path("shops/<int:pk>/enter/", manage.shop_enter, name="shop_enter"),
    path("shops/<int:pk>/location/", manage.shop_location, name="shop_location"),
    path("plans/", manage.plans, name="plans"),
    path("plans/<int:pk>/", manage.plans, name="plan_edit"),
    path("plans/<int:pk>/delete/", manage.plan_delete, name="plan_delete"),
    path("payments/", manage.payments, name="payments"),
    path("requests/", manage.join_requests, name="requests"),
    path("requests/<int:pk>/", manage.join_request_toggle, name="request_toggle"),
    path("site/", manage.site_settings, name="site"),
], "manage")

urlpatterns = [
    path("", public.home, name="home"),
    path("join/", public.join, name="join"),
    path("map/", public.shops_map, name="shops_map"),
    path("map/data.json", public.shops_map_data, name="shops_map_data"),
    path("s/<slug:slug>/", public.shop_detail, name="shop"),
    path("s/<slug:slug>/qr.png", public.shop_qr, name="shop_qr"),
    path("s/<slug:slug>/qr/print/", public.shop_qr_print, name="shop_qr_print"),
    path("login/", auth.login_view, name="login"),
    path("logout/", auth.logout_view, name="logout"),
    path("p/<str:token>/", auth.magic_login, name="magic_login"),
    path("pay/callback/", pay.callback, name="pay_callback"),
    path("pay/mock/<str:ref>/", pay.mock_gateway, name="pay_mock"),
    path("pay/result/<str:ref>/", pay.result, name="pay_result"),
    path("panel/", include(panel_urls)),
    path("manage/", include(manage_urls)),
]
