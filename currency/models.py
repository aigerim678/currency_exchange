from django.db import models


class Currency(models.Model):
    currency_code = models.CharField("Code", max_length=3, unique=True)
    currency_full_name = models.CharField("Full Name", max_length=240)
    sign = models.CharField("Sign", max_length=10)

    def __str__(self):
        
        return self.currency_full_name
    

class ExchangeRate(models.Model):
    base_currency = models.ForeignKey(Currency, related_name='base_rates', on_delete=models.CASCADE)
    target_currency = models.ForeignKey(Currency, related_name='target_rates', on_delete=models.CASCADE)
    rate = models.DecimalField("Rate", max_digits=12, decimal_places=6)

    class Meta:
        unique_together = ('base_currency', 'target_currency')
    def __str__(self):
        return f"{self.base_currency.currency_code} to {self.target_currency.currency_code}: {self.rate}"