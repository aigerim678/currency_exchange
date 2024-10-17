from django.urls import path
from .views import CurrencyDetailView, CurrencyExchangeView, CurrencyView, ExchangeView, ExchangeDetailView

urlpatterns = [
    path('currencies/', CurrencyView.as_view(), name='currency-list'),
    path('exchangeRates/', ExchangeView.as_view(), name='rate-list'),
    path('exchange/', CurrencyExchangeView.as_view(), name='currency-exchange'),
    path('currency/<str:currency_code>/', CurrencyDetailView.as_view(), name='currency-detail'),  # Новый URL для получения конкретной валюты
    path('exchangeRate/<str:currency_pair>/', ExchangeDetailView.as_view(), name='rates-detail'),
]
