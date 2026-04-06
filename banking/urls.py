from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "banking"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("credit/", views.credit_view, name="credit"),
    path("debit/", views.debit_view, name="debit"),
    path("pay/", views.payment_view, name="payment"),
    path("receipt/<int:pk>/", views.receipt, name="receipt"),
    path("receipt/<int:pk>/save/", views.save_receipt, name="save_receipt"),
    path("receipt/<int:pk>/unsave/", views.unsave_receipt, name="unsave_receipt"),
    path("history/", views.history, name="history"),
]
