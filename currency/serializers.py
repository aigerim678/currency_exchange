
from rest_framework import serializers

from currency.models import Currency, ExchangeRate



class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'currency_code', 'currency_full_name', 'sign']


class ExchangeRateSerializer(serializers.ModelSerializer):
    base_currency = CurrencySerializer()  # Вложенный сериализатор для базовой валюты
    target_currency = CurrencySerializer()  # Вложенный сериализатор для целевой валюты

    class Meta:
        model = ExchangeRate
        fields = ['base_currency', 'target_currency', 'rate']

    def create(self, validated_data):
        base_currency_data = validated_data.pop('base_currency')
        target_currency_data = validated_data.pop('target_currency')
        base_currency = Currency.objects.get(**base_currency_data)
        target_currency = Currency.objects.get(**target_currency_data)
        exchange_rate = ExchangeRate.objects.create(
            base_currency=base_currency,
            target_currency=target_currency,
            **validated_data
        )
        return exchange_rate
    

