from django.contrib import admin
from .models import Currency, ExchangeRate
# Register your models here.

admin.site.register(Currency)
admin.site.register(ExchangeRate)