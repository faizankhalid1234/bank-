from django.urls import path

from . import api_views

urlpatterns = [
    path("csrf/", api_views.CsrfView.as_view()),
    path("branding/", api_views.BrandingView.as_view()),
    path("auth/login/", api_views.LoginView.as_view()),
    path("auth/demo-login/", api_views.DemoLoginView.as_view()),
    path("auth/logout/", api_views.LogoutView.as_view()),
    path("auth/register/request/", api_views.RegisterRequestView.as_view()),
    path("auth/register/confirm/", api_views.RegisterConfirmView.as_view()),
    path("me/", api_views.MeView.as_view()),
    path("pay/", api_views.PaymentView.as_view()),
    path("receipt/<int:pk>/", api_views.ReceiptDetailView.as_view()),
    path("receipt/<int:pk>/save/", api_views.SaveReceiptView.as_view()),
    path("receipt/<int:pk>/unsave/", api_views.UnsaveReceiptView.as_view()),
    path("history/", api_views.HistoryView.as_view()),
]
