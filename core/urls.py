"""
Core App URLs
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('help/', views.HelpCenterView.as_view(), name='help'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('faq/', views.FAQView.as_view(), name='faq'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('licenses/', views.LicensesView.as_view(), name='licenses'),
    path('help/seller/', views.SellerGuideView.as_view(), name='seller-guide'),
    path('help/buyer/', views.BuyerGuideView.as_view(), name='buyer-guide'),
    path('help/payments/', views.PaymentsGuideView.as_view(), name='payments-guide'),
    path('help/account/', views.AccountGuideView.as_view(), name='account-guide'),
]
